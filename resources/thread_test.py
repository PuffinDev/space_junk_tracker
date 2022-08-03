
# Python program killing
# threads using stop
# flag
 
from threading import Thread, Event
import time

class StoppableThread(Thread):
    def __init__(self,  *args, **kwargs):
        super(StoppableThread, self).__init__(*args, **kwargs)
        self._stop_event = Event()

    def stop(self):
        self._stop_event.set()

    @property
    def stopped(self):
        return self._stop_event.is_set()
class MyApp():
    def __init__(self) -> None:
        pass

    def update(self):
        while True:
            print('updating everything')
            time.sleep(0.1)

    def density_update(self):
        while True:
            print('updating densities')
            time.sleep(0.3)

    def start_threads(self):
        self.update_thread = StoppableThread(target=self.update)
        self.update_thread.start()
        self.density_update_thread = StoppableThread(target=self.density_update)
        self.density_update_thread.start()

    def restart_threads(self):
        print('stopping threads')
        self.update_thread.stop()
        self.update_thread.join()
        self.density_update_thread.stop()
        self.density_update_thread.join()
        self.print("Changed dataset")
        self.start_threads()
        

    def update_2(self, stop):
        while True:
            time.sleep(0.2)
            print('update running')
            if stop():
                    break

    def density_2(self, stop):
        while True:
            time.sleep(0.3)
            print('density running')
            if stop():
                    break

    def start_threads_2(self):
        print('starting')
        self.stop_threads = False
        self.t1 = Thread(target = self.update_2, args =(lambda : self.stop_threads, ))
        self.t1.start()
        self.t2 = Thread(target = self.density_2, args =(lambda : self.stop_threads, ))
        self.t2.start()

    def restart_threads_2(self):
        print('stopping')
        self.stop_threads = True
        self.t1.join()
        self.t2.join()
        print('stopped')
        time.sleep(1)
        self.start_threads_2()

    def main(self):
        self.start_threads_2()
        while True:
            time.sleep(5)
            self.restart_threads_2()

if __name__ == "__main__":
    my_app = MyApp()
    my_app.main()