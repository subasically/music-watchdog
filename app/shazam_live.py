##############################
# NOT USED IN THE APP        #
# MAYBE USEFUL IN THE FUTURE #
##############################

# import asyncio
# import threading
# import time
# from watchdog.observers import Observer
# from watchdog.events import FileSystemEventHandler
# from shazamio import Shazam

# path_to_dir = "./to_process"
# music_extension = "mp3"
# music_segment_duration = 10  # seconds
# file_check_change = 2500  # milliseconds
# output_file = "./songs.txt"

# shazam = Shazam()


# def create_callback():
#     # check create and wait when fragment should recorded
#     def on_create(event):
#         source_path = event.src_path
#         file_name = source_path.split(dir, 1)[1]
#         if file_name.split(".")[1] == music_extension:
#             print(f"{file_name} was just created, wait when record ends...")

#             loop = asyncio.new_event_loop()
#             threading.Thread(daemon=True, target=loop.run_forever).start()

#             async def sleep_and_run():
#                 await asyncio.sleep(music_segment_duration)
#                 await recognize(path_to_dir + file_name)

#             asyncio.run_coroutine_threadsafe(sleep_and_run(), loop)
#     return on_create


# async def recognize(file_path):
#     out = await shazam.recognize_song(file_path)
#     if "track" in out:
#         with open(output_file, 'r+') as write_file:
#             current_song = out["track"]["subtitle"] + " - " + out["track"]["title"]
#             if any(current_song == x.rstrip('\r\n') for x in write_file):
#                 print(f"[{file_path}]: Duplicate ({current_song})")
#             else:
#                 print(f"[{file_path}]: New song: {current_song}")
#                 write_file.write(current_song + '\n')
#     else:
#         print(f"[{file_path}]: Undefined segment :(")


# if __name__ == "__main__":
#     event_handler = FileSystemEventHandler()
#     event_handler.on_created = create_callback()

#     observer = Observer()
#     observer.schedule(event_handler, path_to_dir, recursive=True)

#     print("Waiting for changes...")

#     observer.start()

#     try:
#         while True:
#             time.sleep(file_check_change)
#     except KeyboardInterrupt:
#         observer.stop()
#     observer.join()
