"""Marqo integration handlers for the sync service."""
import os
import logging
import marqo
import re
import traceback
import asyncio
from typing import Dict, Any, List, Optional, Union, Tuple, Set
import json

from .config import SyncConfig
from .env_config import env_config

# Try to import resource manager functions, fallback if not available
try:
    from .resource_manager import get_optimal_batch_size, should_throttle, wait_for_resources, log_resource_status
    RESOURCE_MANAGER_AVAILABLE = True
except ImportError:
    RESOURCE_MANAGER_AVAILABLE = False
    # Fallback functions
    def get_optimal_batch_size():
        return 32  # Conservative default
    
    def should_throttle():
        return False  # No throttling if resource manager not available
    
    async def wait_for_resources(timeout=30.0):
        return True  # Always proceed if resource manager not available
    
    def log_resource_status():
        pass  # No logging if resource manager not available

logger = logging.getLogger(__name__)

# Log resource manager availability
if RESOURCE_MANAGER_AVAILABLE:
    logger.info("Resource manager available - enhanced resource monitoring enabled")
else:
    logger.warning("Resource manager not available - using fallback resource management")

def ensure_specialized_index(client: marqo.Client, index_name: str, settings: Optional[Dict[str, Any]] = None) -> None:
    try:
        desired_settings = settings or {"model": "hf/all_datasets_v4_MiniLM-L6"}
        try:
            existing_index = client.get_index(index_name)
            logger.info(f"Index {index_name} exists")
        except Exception as e:
            error_str = str(e).lower()
            if "not found" in error_str or "does not exist" in error_str:
                logger.info(f"Index {index_name} does not exist, creating...")
                client.create_index(index_name, settings_dict=desired_settings)
                logger.info(f"Successfully created index {index_name}")
            else:
                logger.warning(f"Error checking index {index_name}: {e}")
    except Exception as e:
        logger.error(f"Error ensuring index exists: {e}")
        raise

def ensure_index_exists(client: marqo.Client, config: SyncConfig) -> None:
    """Ensure Marqo index exists with proper settings, preserving existing data when possible."""
    try:
        force_recreate = env_config.get_force_index_recreate()
        
        # Desired settings for the index
        desired_settings: Dict[str, Any] = {
            "model": "hf/all_datasets_v4_MiniLM-L6"
        }
        
        # Check if index exists
        try:
            existing_index = client.get_index(config.index_name)
            logger.info(f"Index {config.index_name} exists")
            
            if force_recreate:
                logger.warning(f"FORCE_INDEX_RECREATE is enabled - deleting and recreating index {config.index_name}")
                logger.warning("This will DELETE ALL EXISTING DATA in the index!")
                client.delete_index(config.index_name)
                logger.info(f"Deleted index {config.index_name}")
                # Fall through to create new index
            
            else:
                try:
                    # Get current settings
                    current_settings = existing_index.get('settings', {})
                    logger.debug(f"Current index settings: {current_settings}")
                    logger.debug(f"Desired index settings: {desired_settings}")
                    
                    # Check if settings match what we want
                    settings_match = True
                    for key, desired_value in desired_settings.items():
                        current_value = current_settings.get(key)
                        if current_value != desired_value:
                            logger.info(f"Setting mismatch for '{key}': current='{current_value}', desired='{desired_value}'")
                            settings_match = False
                    
                    if settings_match:
                        logger.info(f"Index {config.index_name} has correct settings, preserving existing data")
                        logger.debug(f"Returning early from ensure_index_exists for {config.index_name}")
                        return
                    else:
                        logger.warning(f"Index {config.index_name} has incorrect settings, but preserving data for incremental sync")
                        logger.info("The incremental sync system will handle updates without data loss")
                        logger.info("To force recreation with correct settings, set FORCE_INDEX_RECREATE=true")
                        logger.debug(f"Returning early from ensure_index_exists for {config.index_name}")
                        return
                        
                except Exception as settings_error:
                    logger.warning(f"Error checking index settings for {config.index_name}: {settings_error}")
                    logger.info("Preserving existing index and continuing with incremental sync")
                    return
                
        except Exception as e:
            # Check if this is a "index not found" error or something else
            error_str = str(e).lower()
            if "not found" in error_str or "does not exist" in error_str:
                logger.info(f"Index {config.index_name} does not exist, will create new one")
            else:
                logger.warning(f"Error checking index {config.index_name}: {e}")
                logger.info("Assuming index does not exist, will create new one")
        
        # Create new index with desired settings
        logger.info("Creating index with absolute minimal Marqo v2.16.1 settings")
        client.create_index(config.index_name, settings_dict=desired_settings)
        logger.info(f"Successfully created index {config.index_name}")
        
    except Exception as e:
        logger.error(f"Error ensuring index exists: {e}")
        raise

def check_marqo_compatibility(client: marqo.Client) -> None:
    """Check if Marqo server is compatible with our requirements."""
    try:
        # Try to get Marqo version - different methods for different versions
        version = 'unknown'
        
        # Try the newer method first
        try:
            stats = client.get_stats()
            version = stats.get('marqo_version', 'unknown')
        except AttributeError:
            # Try alternative method for older versions
            try:
                # Some versions might have different method names
                if hasattr(client, 'health'):
                    health = client.health()
                    version = health.get('version', 'unknown')
                elif hasattr(client, 'info'):
                    info = client.info()
                    version = info.get('version', 'unknown')
            except Exception:
                pass
        
        logger.info(f"Connected to Marqo version: {version}")
        
        # Add compatibility checks here if needed
        # For example, minimum version requirements
        
    except Exception as e:
        logger.warning(f"Could not check Marqo compatibility: {e}")
        # Don't raise, just warn

def index_document_metadata(client: marqo.Client, index_name: str, file_path: str, metadata: Dict[str, Any]) -> bool:
    """Index a document with metadata only (for large files).
    
    Args:
        client: Marqo client
        index_name: Name of the index
        file_path: Path to the file
        metadata: File metadata
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Process metadata to ensure only numeric values are at top level
        # This avoids Marqo errors with string fields
        processed_metadata = {}
        string_metadata = {}
        
        for key, value in metadata.items():
            # If it's a number, keep it at top level
            if isinstance(value, (int, float)):
                processed_metadata[key] = value
            # If it's a string or other type, put it in a nested structure
            else:
                string_metadata[key] = value
        
        # Add the string metadata under a safe field
        if string_metadata:
            processed_metadata['string_fields'] = string_metadata
            
        document = {
            'filepath': file_path,
            '_id': file_path,
            'metadata': processed_metadata,
            'is_large_file': True,
            'content': f"Large file: {os.path.basename(file_path)}"
        }
        logger.info(f"Document structure: {document}")
        
        try:
            logger.info(f"Attempting to index large file to Marqo: {file_path}")
            logger.info(f"Index name: {index_name}")
            logger.info(f"Marqo client: {type(client)}")
            
            # For Marqo 3.x, tensor_fields must be explicitly specified
            result = client.index(index_name).add_documents(
                documents=[document],
                tensor_fields=['content']  # Explicitly specify content field for vectorization
            )
            
            logger.info(f"Marqo response: {result}")
            
            # Check for errors in the result
            if result and 'errors' in result and result['errors']:
                logger.error(f"Marqo returned errors during indexing of {file_path}: {result['errors']}")
                return False
            
            # SUCCESS
            logger.info(f"SUCCESS: Indexed large file metadata: {file_path}")
            return True
                
        except Exception as e:
            logger.error(f"EXCEPTION during large file indexing for {file_path}: {e}")
            logger.error(f"Exception type: {type(e).__name__}")
            logger.error(f"Exception details: {str(e)}")
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")
            return False
    except Exception as e:
        logger.error(f"Error indexing metadata for {file_path}: {e}")
        logger.error(f"Exception type: {type(e).__name__}")
        logger.error(f"Exception details: {str(e)}")
        import traceback
        logger.error(f"Full traceback: {traceback.format_exc()}")
        return False

async def index_document_chunks(client: marqo.Client, index_name: str, file_path: str, 
                         chunks: List[str], metadata: Dict[str, Any]) -> bool:
    """Index document chunks with content.
    
    Args:
        client: Marqo client
        index_name: Name of the index
        file_path: Path to the file
        chunks: List of content chunks
        metadata: File metadata
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Create documents for each chunk
        documents = []
        for i, chunk in enumerate(chunks):
            doc_id = f"{file_path}#chunk{i}"
            
            # Process metadata to ensure only numeric values are at top level
            # This avoids Marqo errors with string fields
            processed_metadata = {}
            string_metadata = {}
            
            for key, value in metadata.items():
                # If it's a number, keep it at top level
                if isinstance(value, (int, float)):
                    processed_metadata[key] = value
                # If it's a string or other type, put it in a nested structure
                else:
                    string_metadata[key] = value
            
            # Add the string metadata under a safe field
            if string_metadata:
                processed_metadata['string_fields'] = string_metadata
            
            # Add chunk metadata
            processed_metadata['chunk_index'] = i
            processed_metadata['total_chunks'] = len(chunks)
            
            document = {
                'filepath': file_path,
                '_id': doc_id,
                'metadata': processed_metadata,
                'is_large_file': False,
                'content': chunk
            }
            documents.append(document)
        
        logger.info(f"Successfully created {len(documents)} documents for: {file_path}")
        
        # Batch index the chunks with resource-aware batching
        batch_size = get_optimal_batch_size()
        successful_batches = 0
        total_batches = (len(documents) + batch_size - 1) // batch_size
        
        logger.info(f"Starting resource-aware batch indexing: {total_batches} batches (size: {batch_size}) for {file_path}")
        
        for i in range(0, len(documents), batch_size):
            # Check if we should throttle before processing this batch
            if should_throttle():
                logger.info("System under pressure, waiting for resources...")
                if not await wait_for_resources(timeout=30.0):
                    logger.warning("Timeout waiting for resources, proceeding with reduced batch size")
                    batch_size = min(batch_size, 8)  # Fallback to very small batch
            
            batch = documents[i:i + batch_size]
            batch_num = i//batch_size + 1
            logger.info(f"Indexing batch {batch_num}/{total_batches} with {len(batch)} documents for: {file_path}")
            
            try:
                logger.info(f"Calling Marqo API for batch {batch_num}: {file_path}")
                logger.info(f"Index name: {index_name}")
                logger.info(f"Batch size: {len(batch)}")
                
                # For Marqo 3.x, tensor_fields must be explicitly specified
                result = client.index(index_name).add_documents(
                    documents=batch,
                    tensor_fields=['content']  # Explicitly specify content field for vectorization
                )
                
                logger.info(f"Marqo API response for batch {batch_num}: {result}")
                
                # Check for errors in the result
                if result and 'errors' in result and result['errors']:
                    logger.error(f"Marqo returned errors for batch {batch_num} of {file_path}: {result['errors']}")
                    continue  # Skip this batch but continue with others
                
                successful_batches += 1
                logger.info(f"SUCCESS: Indexed batch {batch_num}/{total_batches} for file: {file_path}")
                
                # Brief pause between batches to allow system to recover
                await asyncio.sleep(0.1)
                
            except Exception as e:
                logger.error(f"EXCEPTION indexing batch {batch_num} for file {file_path}: {e}")
                logger.error(f"Exception type: {type(e).__name__}")
                logger.error(f"Exception details: {str(e)}")
                import traceback
                logger.error(f"Full traceback: {traceback.format_exc()}")
                # Continue with next batch instead of failing completely
                continue
        
        # Return success only if ALL batches were successful
        if successful_batches == total_batches and total_batches > 0:
            logger.info(f"SUCCESS: Indexed file: {file_path} (chunks={len(chunks)})")
            return True
        else:
            logger.error(f"FAILED: Only {successful_batches}/{total_batches} batches succeeded for {file_path}")
            return False
            
    except Exception as e:
        logger.error(f"Error indexing chunks for {file_path}: {e}")
        logger.error(f"Exception type: {type(e).__name__}")
        logger.error(f"Exception details: {str(e)}")
        import traceback
        logger.error(f"Full traceback: {traceback.format_exc()}")
        return False

def delete_document(client: marqo.Client, index_name: str, file_path: str) -> bool:
    """Delete all documents associated with a file path.
    
    Args:
        client: Marqo client
        index_name: Name of the index
        file_path: Path to the file
        
    Returns:
        True if successful, False otherwise
    """
    try:
        logger.info(f"Removing file from index: {file_path}")
        
        # Get all documents for this file
        try:
            search_results = client.index(index_name).search(
                f"filepath:{file_path}",
                limit=1000
            )
            
            if search_results['hits']:
                # Delete documents by ID
                doc_ids = [hit['_id'] for hit in search_results['hits']]
                logger.info(f"Found {len(doc_ids)} documents to delete for file: {file_path}")
                
                result = client.index(index_name).delete_documents(doc_ids)
                
                # Check for errors in the result
                if result and 'errors' in result and result['errors']:
                    logger.error(f"Marqo returned errors during deletion of {file_path}: {result['errors']}")
                    return False
                
                logger.info(f"Successfully removed {len(doc_ids)} documents from index for file: {file_path}")
                return True
            else:
                logger.debug(f"No documents found in index for file: {file_path}")
                return True  # Consider this a success as there's nothing to delete
                
        except Exception as e:
            logger.error(f"EXCEPTION during document deletion for {file_path}: {e}")
            logger.error(f"Exception type: {type(e).__name__}")
            logger.error(f"Exception details: {str(e)}")
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")
            return False
            
    except Exception as e:
        logger.error(f"Error removing documents from index for {file_path}: {e}")
        logger.error(f"Exception type: {type(e).__name__}")
        logger.error(f"Exception details: {str(e)}")
        import traceback
        logger.error(f"Full traceback: {traceback.format_exc()}")
        return False
