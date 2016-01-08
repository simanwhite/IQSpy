import multiprocessing
import os
import time
import iqspy_gui
import iqshark


# def capture_process_wrapper(user_inputs, data_q):
#     # user_inputs = {'interface': 'asdf', 'ipaddress': 'iqxs8499', 'port': '24000'}
#     for each_scpi in iqshark.capture_scpi(user_inputs['interface'],
#                                           user_inputs['ipaddress'],
#                                           user_inputs['port']):
#         data_q.put(each_scpi)


def capture_process_wrapper(user_inputs, data_q):
    # user_inputs = {'interface': 'asdf', 'ipaddress': 'iqxs8499', 'port': '24000'}
    for each_scpi in iqshark.capture_scpi_all_ports(user_inputs['interface'],
                                                    user_inputs['ipaddress']):
        data_q.put(each_scpi)


def data_saving_process(data_q):
    output_fp = None
    output_file_open_flag = False
    while True:
        item = data_q.get()
        if item:
            if not output_file_open_flag:
                output_fp = open('./capture.txt', 'ab')
                output_file_open_flag = True
                print 'file opened!'
            try:
                output_fp.write(item + '\n')
            except AttributeError:
                print 'No output_fp yet'
        else:
            try:
                print 'try to save file'
                output_file_open_flag = False
                output_fp.close()
                print 'file saved'
            except AttributeError:
                print 'file save error'
                pass


def main():
    shared_q_control = multiprocessing.Queue()
    shared_q_data = multiprocessing.Queue()

    gui_process = multiprocessing.Process(target=iqspy_gui.show, args=(shared_q_control,))
    # gui_process.daemon = True
    gui_process.start()

    data_process = multiprocessing.Process(target=data_saving_process, args=(shared_q_data,))
    data_process.daemon = True
    data_process.start()

    shark_process = None
    while True:
        item = shared_q_control.get()
        if isinstance(item, dict):
            print 'begin btn pressed'
            shark_process = multiprocessing.Process(target=capture_process_wrapper,
                                                    args=(item, shared_q_data))
            # shark_process.daemon = True
            shark_process.start()

        elif item == 'stop':
            print 'stop btn pressed'
            shark_process.terminate()
            shared_q_data.put(None)  # indicate data process to save the file
        elif item == 'destroy':
            print 'GUI destroyed'
            if os.path.isfile('./capture.txt'):
                os.system('taskkill /F /IM notepad++.exe /T')
                os.system(r'"Notepad++\notepad++.exe" -n999999999 -nosession capture.txt')
            try:
                shared_q_data.put(None)  # indicate data process to save the file
                if data_process.is_alive():
                    while not shared_q_data.empty():
                        print 'wait for data_q to empty'
                    time.sleep(0.5)
                    data_process.terminate()
                    print 'data process killed'
                if shark_process.is_alive():
                    shark_process.terminate()
                    print 'shark process killed'
                if gui_process.is_alive():
                    gui_process.terminate()
                    print 'gui process killed'
                os.system('taskkill /F /IM tshark.exe /T')
            except AttributeError:
                pass
            break


if __name__ == '__main__':
    main()
