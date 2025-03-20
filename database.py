from pymongo import MongoClient
from datetime import datetime
import json
from bson import ObjectId

class AccessibilityDB:
    def __init__(self):
        try:
            self.client = MongoClient('mongodb://localhost:27017/',
                                    serverSelectionTimeoutMS=5000)
            self.client.server_info()
            self.db = self.client['accessibility_tests']
            
            # Separate collections for test runs and page results
            self.test_runs = self.db['test_runs']
            self.page_results = self.db['page_results']
            
            # Create indexes
            self.page_results.create_index([('url', 1), ('test_run_id', 1)])
            self.page_results.create_index('timestamp')
            self.test_runs.create_index('timestamp')
        except Exception as e:
            print(f"Failed to connect to MongoDB: {e}")
            raise

    def start_new_test_run(self, settings, documentation=None):
        """
        Create a new test run and return its ID
        
        Args:
            settings: Dictionary of test run settings
            documentation: Optional dictionary of test documentation objects
        
        Returns:
            str: The ID of the created test run
        """
        test_run = {
            'timestamp_start': datetime.now().isoformat(),
            'status': 'in_progress',
            'settings': settings
        }
        
        # Add documentation if provided
        if documentation:
            test_run['documentation'] = documentation
            print(f"Including documentation for {len(documentation)} test types in test run")
        
        result = self.test_runs.insert_one(test_run)
        return str(result.inserted_id)

    def save_page_result(self, test_run_id, url, page_result):
        """Save individual page result"""
        try:
            # Prepare the document
            document = {
                'test_run_id': test_run_id,
                'url': url,
                'timestamp': datetime.now().isoformat(),
                'results': page_result
            }
            
            # Update or insert the page result
            return self.page_results.update_one(
                {
                    'test_run_id': test_run_id,
                    'url': url
                },
                {'$set': document},
                upsert=True
            )
        except Exception as e:
            print(f"Error saving page result: {e}")
            return None

    def complete_test_run(self, test_run_id, summary=None):
        """Mark a test run as complete and add summary data"""
        try:
            update_data = {
                'status': 'completed',
                'timestamp_end': datetime.now().isoformat()
            }
            if summary:
                update_data['summary'] = summary

            self.test_runs.update_one(
                {'_id': ObjectId(test_run_id)},
                {'$set': update_data}
            )
        except Exception as e:
            print(f"Error completing test run: {e}")

    def get_page_results(self, test_run_id):
        """Get all page results for a specific test run"""
        try:
            return list(self.page_results.find(
                {'test_run_id': test_run_id},
                {'_id': 0}
            ))
        except Exception as e:
            print(f"Error getting page results: {e}")
            return []

    def export_to_json(self, filename, test_run_id):
        """Export results for a specific test run to JSON file"""
        try:
            # Get test run info
            test_run = self.test_runs.find_one(
                {'_id': ObjectId(test_run_id)},
                {'_id': 0}
            )
            
            # Get all page results
            page_results = self.get_page_results(test_run_id)
            
            # Combine into one document
            full_results = {
                'test_run': test_run,
                'pages': {result['url']: result['results'] for result in page_results}
            }
            
            with open(filename, 'w') as f:
                json.dump(full_results, f, indent=2, default=str)
        except Exception as e:
            print(f"Error exporting to JSON: {e}")

    def clear_database(self):
        """Clear all collections in the database"""
        try:
            self.test_runs.drop()
            self.page_results.drop()
            
            # Recreate indexes
            self.page_results.create_index([('url', 1), ('test_run_id', 1)])
            self.page_results.create_index('timestamp')
            self.test_runs.create_index('timestamp')
            
            print("Database cleared successfully")
        except Exception as e:
            print(f"Error clearing database: {e}")



    def __del__(self):
        if hasattr(self, 'client'):
            self.client.close()