
# Python program killing
# threads using stop
# flag
 
import threading
import time
 
def run(stop):
    while True:
        print('thread running')
        time.sleep(0.2)
        if stop():
                break

def main():
    while True:
        stop_threads = False
        t1 = threading.Thread(target = run, args =(lambda : stop_threads, ))
        t1.start()
        print('thread started')
        time.sleep(1)
        stop_threads = True
        t1.join()
        print('thread killed')
        time.sleep(1)

main()