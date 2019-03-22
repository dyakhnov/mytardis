from datetime import datetime, timedelta
import shelve

now = datetime.now(tz=None)
file_data = shelve.open('celerybeat-schedule') # Name of the file used by PersistentScheduler to store the last run times of periodic tasks.

if 'entries' in file_data:
  for task_name, task in file_data['entries'].items():
    try:
      assert now  < task.last_run_at.replace(tzinfo=None) + task.schedule.run_every
    except AttributeError:
      assert timedelta() < task.schedule.remaining_estimate(task.last_run_at)
