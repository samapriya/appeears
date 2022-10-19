# Task info

The task info tool is a quick way to look at all tasks, or a specic task by task ID or task status type. The tool is designed to also return task name which is currently not returned when using a specific task ID for running a search. The task info tool groups all task types by processing status and returns the final result.

![appeears_taskinfo](https://user-images.githubusercontent.com/6677629/196685258-fdf25d0f-24e6-46ef-a0a4-8c2e5bad3cce.gif)

```
appeears task-info -h
usage: appeears task-info [-h] [--tid TID] [--status STATUS]

optional arguments:
  -h, --help       show this help message and exit

Optional named arguments:
  --tid TID        Task ID
  --status STATUS  Task status processing|done|pending
```
