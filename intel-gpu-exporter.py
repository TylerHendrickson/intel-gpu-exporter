import json
import string
import subprocess
import time

from prometheus_client import (GC_COLLECTOR, PLATFORM_COLLECTOR,
                               PROCESS_COLLECTOR, REGISTRY, Metric,
                               start_http_server)

decoder = json.JSONDecoder()


class DataCollector(object):
    def __init__(self, endpoint):
        self._endpoint = endpoint

    def _parse_output(self, output):
        data = []
        output = output.strip()
        while output:
            doc, decoded_to = decoder.raw_decode(output)
            data.append(doc)
            output = output[decoded_to:].strip()
            if output and output[0] == ',':
                output = output[1:].strip()
        return data

    def collect(self):
        cmd = "/usr/bin/timeout -k 2 2 /usr/bin/intel_gpu_top -J"
        raw_output = subprocess.run(cmd.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE).stdout.decode("utf-8")
        data = self._parse_output(raw_output)

        power_watts = data[1].get("power", {}).get("value", 0.0)
        metric = Metric("intel_gpu_power", "Power utilisation in Watts", "summary")
        metric.add_sample("intel_gpu_power", value=power_watts, labels={})
        yield metric

        render_busy_percent = data[1].get("engines", {}).get("Render/3D/0", {}).get("busy", 0.0)
        metric = Metric("intel_gpu_render_busy_percent", "Render busy utilisation in %", "summary")
        metric.add_sample("intel_gpu_render_busy_percent", value=render_busy_percent, labels={})
        yield metric

        video_busy_percent = data[1].get("engines", {}).get("Video/0", {}).get("busy", 0.0)
        metric = Metric("intel_gpu_video_busy_percent", "Video busy utilisation in %", "summary")
        metric.add_sample("intel_gpu_video_busy_percent", value=video_busy_percent, labels={})
        yield metric

        enhance_busy_percent = data[1].get("engines", {}).get("VideoEnhance/0", {}).get("busy", 0.0)
        metric = Metric("intel_gpu_enhance_busy_percent", "Enhance busy utilisation in %", "summary")
        metric.add_sample("intel_gpu_enhance_busy_percent", value=enhance_busy_percent, labels={})
        yield metric

if __name__ == "__main__":
    host, port = "0.0.0.0:8080".split(':')
    start_http_server(int(port), host)
    REGISTRY.unregister(PROCESS_COLLECTOR)
    REGISTRY.unregister(PLATFORM_COLLECTOR)
    REGISTRY.unregister(GC_COLLECTOR)
    REGISTRY.register(DataCollector(f"http://{host}:{port}/metrics"))
    while True:
        time.sleep(1)
