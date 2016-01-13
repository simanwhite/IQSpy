from Tkinter import *
from ttk import *
import os
import pickle
import iqshark


class App(Frame):
    def __init__(self, parent=None, shared_q=None, **kw):
        Frame.__init__(self, **kw)
        self.parent = parent
        self.shared_q = shared_q

        # button group
        self.button_frame = Frame(self.parent)
        self.stop_button = Button(self.button_frame, text='Stop')
        self.begin_button = Button(self.button_frame, text='Capture')

        # interface group (network connections)
        self.interfaces_frame = Frame(self.parent)
        self.interfaces_combobox = Combobox(self.interfaces_frame)

        # iqxs info group
        self.iqxsinfo_frame = Frame(self.parent)
        self.iqxsinfo_ip_entry = Entry(self.iqxsinfo_frame, width=20)
        self.iqxsinfo_port_combo = Combobox(self.iqxsinfo_frame, values=['24000', '24100', '24200'])

        self.status_label = Label(self.parent)
        self.bind('<Destroy>', self.destroy_handler)

        # privates
        self._user_inputs_storage_file = './previous_gui_inputs.pickle'
        self._ipaddress_textvar = StringVar()

        # layout the widgets
        self.create_widgets()
        self.restore_previous_inputs()

    def destroy_handler(self, event):
        print event  # just have to use it
        # send a 'destroy' signal to the control queue
        if self.shared_q:
            self.shared_q.put('destroy')

    # def __del__(self):  # if I collect user input data here, it will give me t TclError. Don't know why.
    #     # put down the user inputs of the GUI now
    #     gui_inputs = self.collect_user_inputs()
    #     with open(self._user_inputs_storage_file, 'w') as fp:
    #         pickle.dump(gui_inputs, fp)

    def create_widgets(self):
        # combobox group for network connections
        interfaces_frame = self.interfaces_frame
        interfaces_frame.pack()
        interfaces_label = Label(interfaces_frame, text='Select a network connection: ')
        interfaces_label.pack(side=LEFT)
        interfaces_combobox = self.interfaces_combobox
        interfaces_combobox['values'] = iqshark.get_interfaces()
        interfaces_combobox.current(0)
        interfaces_combobox['width'] = 40
        interfaces_combobox.pack(side=LEFT)

        # the group for iqxstream info
        iqxsinfo_frame = self.iqxsinfo_frame
        iqxsinfo_frame.pack()
        iqxsinfo_ip_label = Label(iqxsinfo_frame, text='IQxstream IP Address: ')
        iqxsinfo_ip_label.pack(side=LEFT)
        iqxsinfo_ip_entry = self.iqxsinfo_ip_entry
        iqxsinfo_ip_entry['textvariable'] = self._ipaddress_textvar
        iqxsinfo_ip_entry.pack(side=LEFT)
        # iqxsinfo_port_label = Label(iqxsinfo_frame, text='Port: ')
        # iqxsinfo_port_label.pack(side=LEFT)
        iqxsinfo_port_combo = self.iqxsinfo_port_combo
        iqxsinfo_port_combo.current(0)
        # iqxsinfo_port_combo.pack(side=LEFT)

        # button group
        self.button_frame.pack()
        begin_button = self.begin_button
        begin_button['command'] = self.begin_btn_handler
        begin_button.pack(side=LEFT)
        stop_button = self.stop_button
        stop_button['state'] = DISABLED
        stop_button['command'] = self.stop_btn_handler
        stop_button.pack(side=LEFT)

        # Status label
        self.status_label.pack()

    def begin_btn_handler(self):
        # disable input widgets
        self.begin_button['state'] = DISABLED
        self.interfaces_combobox.state(['disabled'])
        self.iqxsinfo_ip_entry.state(['disabled'])
        self.iqxsinfo_port_combo.state(['disabled'])

        self.stop_button['state'] = NORMAL
        self.status_label['text'] = 'Capturing...(Stop and close to show log)'

        user_inputs = self.collect_user_inputs()
        if self.shared_q:
            self.shared_q.put(user_inputs)  # put a dict into ctrl_q to indicate capture begins
        return

    def stop_btn_handler(self):
        if self.shared_q:
            self.shared_q.put('stop')
        # enable input widgets
        self.begin_button['state'] = NORMAL
        self.interfaces_combobox.state(['!disabled'])
        self.iqxsinfo_ip_entry.state(['!disabled'])
        self.iqxsinfo_port_combo.state(['!disabled'])

        self.stop_button['state'] = DISABLED
        self.status_label['text'] = 'Capture Stopped.'
        return

    def collect_user_inputs(self):
        in_args = {'interface': str(self.interfaces_combobox.current() + 1),  # use index to avoid failure on Chinese OS
                   'ipaddress': self._ipaddress_textvar.get(),
                   'port': self.iqxsinfo_port_combo['values'][self.iqxsinfo_port_combo.current()],
                   }
        return in_args

    def restore_previous_inputs(self):
        if os.path.isfile(self._user_inputs_storage_file):
            with open(self._user_inputs_storage_file, 'r') as fp:
                previous_user_inputs = pickle.load(fp)
            if previous_user_inputs['interface'] in self.interfaces_combobox['values']:
                cur_index = self.interfaces_combobox['values'].index(previous_user_inputs['interface'])
                self.interfaces_combobox.current(cur_index)
            if previous_user_inputs['port'] in self.iqxsinfo_port_combo['values']:
                cur_index = self.iqxsinfo_port_combo['values'].index(previous_user_inputs['port'])
                self.iqxsinfo_port_combo.current(cur_index)
            self._ipaddress_textvar.set(previous_user_inputs['ipaddress'])
        return

    def before_quit(self):
        # collect the user input data into a pickle
        gui_inputs = self.collect_user_inputs()
        with open(self._user_inputs_storage_file, 'w') as fp:
            pickle.dump(gui_inputs, fp)
        try:
            self.parent.destroy()
        except AttributeError:
            pass


def show(shared_q):
    root = Tk()
    app = App(parent=root, shared_q=shared_q)
    app.master.title('IQSpy - Litepoint')
    root.protocol("WM_DELETE_WINDOW", app.before_quit)
    app.mainloop()


if __name__ == '__main__':
    show(None)
