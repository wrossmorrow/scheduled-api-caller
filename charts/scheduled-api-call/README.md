# scheduled-api-call

![Version: 0.1.0](https://img.shields.io/badge/Version-0.1.0-informational?style=flat-square) ![Type: application](https://img.shields.io/badge/Type-application-informational?style=flat-square) ![AppVersion: 0.1.0](https://img.shields.io/badge/AppVersion-0.1.0-informational?style=flat-square)

Just call an API on a schedule

**Homepage:** <https://github.com/wrossmorrow/scheduled-api-call>

## Maintainers

| Name | Email | Url |
| ---- | ------ | --- |
| W. Ross Morrow | <morrowwr@gmail.com> |  |

## Values

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| args.auth | string | `nil` | special object for HTTP auth, must include "type" and "credentials" keys |
| args.body | object | `{}` | the body of the request, if any; will fail if supplied for get or delete |
| args.fail_on | list | `[]` | response status codes to fail on, matching \^(000|[45]([0-9]{2}|[0-9xX][xX]))$\ |
| args.headers | list | `[]` | additional headers to pass to the request (name/value items) |
| args.host | string | `nil` | this host to call, no scheme (e.g., "google.com") |
| args.insecure | bool | `false` | use http if true, uses https by default |
| args.method | string | `"get"` | the HTTP method to use, defaults to get |
| args.params | list | `[]` | params to pass to the request (name/value items) |
| args.path | string | `nil` | the path to call, if not specified, will default to "/" |
| args.port | string | `nil` | the port to call, if not specified, will default to 80 or 443 depending on scheme |
| args.retries | int | `0` | number of retries to attempt, defaults to 0 (total requests == retries + 1) |
| args.retry_on | list | `[]` | response status codes to retry on, matching \^(000|[45]([0-9]{2}|[0-9xX][xX]))$\ |
| args.timeout | string | `nil` | request timeout in seconds for each attempt, defaults to 60 |
| cron.annotations | object | `{}` | annotations to apply to the cronjob |
| cron.concurrency | string | `"Forbid"` | The concurrency policy, most like usually restricted to none |
| cron.labels | object | `{}` | labels to apply to the cronjob |
| cron.schedule | string | `nil` | the cron-style schedule to use for the job |
| cron.time_zone | string | `"Etc/UTC"` | the timezone as [listed here](https://en.wikipedia.org/wiki/List_of_tz_database_time_zones) |
| image.name | string | `"scheduled-api-caller"` | image registry to pull from (probably shouldn't be changed) |
| image.pull_policy | string | `"Always"` | image pull policy, Always is likely always fine |
| image.registry | string | `"ghcr.io/wrossmorrow"` | image registry to pull from (probably shouldn't be changed) |
| image.tag | string | `"latest"` | image registry to pull from (like should be changed based on release versioning) |
| jobs.annotations | object | `{}` | annotations to apply to the jobs |
| jobs.backoff_limit | int | `5` | how many times to retry a failed job |
| jobs.completions | int | `1` | how many successful runs to execute overall |
| jobs.env | list | `[]` | environment variables to pass to the jobs |
| jobs.labels | object | `{}` | labels to apply to the jobs |
| jobs.parallelism | int | `1` | how many runs are allowed in parallel |
| jobs.remove_after_seconds | int | `120` | how long to wait before removing completed jobs from kubernetes management |
| jobs.secret | string | `nil` | a secret to use in envFrom for the jobs |
| name | string | `"scheduled-api-call"` | name of the cronjob |
| pods.annotations | object | `{}` | annotations to apply to the pods |
| pods.labels | object | `{}` | labels to apply to the pods |

----------------------------------------------
Autogenerated from chart metadata using [helm-docs v1.13.1](https://github.com/norwoodj/helm-docs/releases/v1.13.1)