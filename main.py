from api_v01 import mp_api_wraper as v1
from api_v03 import mp_api_v3_wrapper as v3
from os import environ
import threading
import numpy
import logging
from time import time


time_start = time()
DOMAIN = 'oqprint'


def main():
    # ==== P1 ===
    # Create api_v1 object
    # Request notifications
    # Store response in variable
    logging.info('Main started')
    access_id, secret_key = v1.MegaplanAuth(DOMAIN).get_key(environ.get('mp_v3_lg'), environ.get('mp_v3_ps'))
    api1 = v1.MegaplanApi(access_id, secret_key, DOMAIN)
    get_notifications_uri = '/BumsCommonApiV01/Informer/notifications.api'
    notifications_json = api1.get_query(get_notifications_uri, {'Group': 'true', 'Limit': 900})
    
    # ==== P2 ===
    # Parse response for task ids
    # Store list of ids in a variable
    def parse_notifications_for_complaints(notifications):
        logging.info(f'Parsing {len(notifications["notifications"])} notifications')
        task_ids = []
        for notification in notifications['notifications']:
            if notification['Subject']['Type'] == 'comment':
                if 'ЖАЛОБА' in notification['Content']['Subject']['Name']:
                    task_ids.append(notification['Content']['Subject']['Id'])
        return task_ids
    
    list_of_ids = parse_notifications_for_complaints(notifications_json)
    logging.info(f'Found {len(list_of_ids)} tasks to mark as read')

    # ==== P3 ===
    # Create api_v3 object
    # Create function that takes list of task_ids and sends request to mark comments as read for each task_id
    # Pass this function and list of ids to function that divides the list and runs tasks in parallel
    def threaded_request(func_obj, arguments, num_of_threads: int = 6):
        """
        Function for launching a lot of requests in parallel by utilizing threads.
        Takes
        :param func_obj: function object - that is going to be run in each thread
        :param arguments: list, tuple, or dict - inside is some information for each instance of func_obj run
        :param num_of_threads: int - number of parallel threads and number of parts to divide arguments to
        :return: None
        """
        def list_splitter(list_obj: list, number: int = num_of_threads) -> list:
            logging.debug(f'{list_obj}')
            split_list = [section.tolist() for section in numpy.array_split(list_obj, number)]
            logging.debug(f'{split_list}')
            return split_list
    
        threads = []
        for i in list_splitter(arguments):
            threads.append(threading.Thread(target=func_obj, args=[i]))
        for thread in threads:
            thread.start()
    
    if list_of_ids:
        logging.info('Connecting to api v3')
        api3 = v3.MegaplanV3(DOMAIN)
        
        def mark_as_read(entity_id):
            logging.debug(f'{entity_id=}')
            for item in entity_id:
                str_id = str(item)
                api3.post_method('task/{entityId}/comments/markAsRead', var_str='{entityId}', var_arg=str_id)
        
        logging.info('Starting multithreaded task')
        threaded_request(mark_as_read, list_of_ids)
    else:
        logging.info('No tasks found to mark as read')
    

if __name__ == '__main__':
    logging.basicConfig(
        filename='logs/main.log',
        level=logging.INFO,
        format='%(asctime)s;%(levelname)s;%(message)s'
    )
    try:
        main()
        time_stop = time()
        logging.info(f'Complete in {time_stop - time_start} seconds')
    except Exception as exc:
        logging.exception(exc)
        raise exc
