{{- define "args" -}}
- --host
- {{ .Values.args.host }}
{{- if .Values.args.port }}
- --port
- "{{ .Values.args.port }}"
{{- end }}
{{- if .Values.args.path }}
- --path
- {{ .Values.args.path }}
{{- end }}
{{- if .Values.args.body }}
- --body
{{- if (kindIs "string" .Values.args.body )}}
- {{ .Values.args.body | quote }}
{{- else }}
- {{ .Values.args.body | toJson | quote }}
{{- end }}
{{- end }}
{{- if .Values.args.params }}
- --params
{{- range .Values.args.params }}
- {{ .name }}={{ .value }}
{{- end }}
{{- end }}
- --method
- {{ .Values.args.method }}
{{- if .Values.args.headers }}
- --headers
{{- range .Values.args.headers }}
- {{ .name }}={{ .value | quote }}
{{- end }}
{{- end }}
{{- if .Values.args.auth }}
- --auth
- {{ .Values.args.auth.type }}
- --credentials
- {{ .Values.args.auth.credentials }}
{{- end }}
{{- if .Values.args.timeout}}
- --timeout
- "{{ .Values.args.timeout }}"
{{- end }}
- --retries
- "{{ .Values.args.retries }}"
{{- if .Values.args.retry_on}}
- --retry-on
{{- range .Values.args.retry_on }}
- "{{ . }}"
{{- end }}
{{- end }}
{{- if .Values.args.fail_on }}
- --fail-on
{{- range .Values.args.fail_on }}
- "{{ . }}"
{{- end }}
{{- end }}
{{- if .Values.args.insecure }}
- --insecure
{{- end }}
{{- end -}}
