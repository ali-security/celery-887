import os

from create_quorum_queues import my_quorum_queue

from celery import Celery
from celery.canvas import group

app = Celery("myapp", broker="amqp://guest@localhost:5672//")

app.conf.worker_quorumq = os.environ.get("WORKER_QUORUMQ", "False").lower() == "true"

if app.conf.worker_quorumq:
    app.conf.task_queues = (my_quorum_queue,)


@app.task
def add(x, y):
    return x + y


@app.task
def identity(x):
    return x


def test():
    if app.conf.worker_quorumq:
        queue = my_quorum_queue.name
    else:
        queue = "celery"

    while True:
        print("Celery Quorum Queue POC")
        print("=======================")
        print("1. Send a simple identity task")
        print("2. Send a group of add tasks")
        print("3. Inspect the active queues")
        print("4. Shutdown Celery worker")
        print("Q. Quit")
        print("Q! Exit")
        choice = input("Enter your choice (1-4 or Q): ")

        if choice == "1":
            payload = f"Hello, {"Quorum" if app.conf.worker_quorumq else "Classic"} Queue!"
            result = identity.si(payload).apply_async(queue=queue)
            print()
            print(f"Task sent with ID: {result.id}")
            print("Task type: identity")
            print(f"Payload: {payload}")

        elif choice == "2":
            tasks = [
                (1, 2),
                (3, 4),
                (5, 6),
            ]
            result = group(
                add.s(*tasks[0]),
                add.s(*tasks[1]),
                add.s(*tasks[2]),
            ).apply_async(queue=queue)
            print()
            print("Group of tasks sent.")
            print(f"Group result ID: {result.id}")
            for i, task_args in enumerate(tasks, 1):
                print(f"Task {i} type: add")
                print(f"Payload: {task_args}")

        elif choice == "3":
            active_queues = app.control.inspect().active_queues()
            print()
            print("Active queues:")
            for worker, queues in active_queues.items():
                print(f"Worker: {worker}")
                for queue in queues:
                    print(f"  - {queue['name']}")

        elif choice == "4":
            print("Shutting down Celery worker...")
            app.control.shutdown()

        elif choice.lower() == "q":
            print("Quitting test()")
            break

        elif choice.lower() == "q!":
            print("Exiting...")
            os.abort()

        else:
            print("Invalid choice. Please enter a number between 1 and 4 or Q to quit.")

        print("\n" + "#" * 80 + "\n")


if __name__ == "__main__":
    app.start()
