# Task info

The task info tool is a quick way to look at all tasks, or a specic task by task ID or task status type. The tool is designed to also return task name which is currently not returned when using a specific task ID for running a search. The task info tool groups all task types by processing status and returns the final result.

![appeears_taskinfo](https://user-images.githubusercontent.com/6677629/196597569-6b880449-819b-4b86-a4ce-9b4715778420.gif)

```
appeears task-info -h
usage: appeears task-info [-h] [--tid TID] [--status STATUS]

optional arguments:
  -h, --help       show this help message and exit

Optional named arguments:
  --tid TID        Task ID
  --status STATUS  Task status processing|done|pending
```
