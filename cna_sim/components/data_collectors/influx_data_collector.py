import datetime
from copy import copy
from dataclasses import dataclass, asdict

from . import DefaultDataCollectorConfig
from .default_data_collector import DefaultDataCollector
from ...core import *
from ...utils import to_timestamp_ns, not_none, default_if_none, shallow_asdict


@dataclass
class InfluxDataCollectorConfig(Config):
    url: str
    token: str
    org: str
    bucket: str
    time_offset: datetime.datetime
    clear_from_start: bool = None
    name: str = None

    def generator(self):
        return lambda ctx: InfluxDataCollector(ctx, **shallow_asdict(self))



class InfluxDataCollector(DefaultDataCollector):
    def __init__(self, context: Context, url, token, org, bucket, time_offset, clear_from_start=None, name=None):
        from influxdb_client import InfluxDBClient, WriteOptions

        super().__init__(context, name)
        self.time_offset = to_timestamp_ns(not_none(time_offset))  # in ns
        self.influx_client = InfluxDBClient(url=not_none(url), token=not_none(token), org=not_none(org))
        self.write_api = self.influx_client.write_api(write_options=WriteOptions(batch_size=1000))
        self.buckets_api = self.influx_client.buckets_api()
        self.bucket = not_none(bucket)

        buckets = self.influx_client.buckets_api().find_bucket_by_name(self.bucket)
        if buckets:
            if default_if_none(clear_from_start, True):
                self.buckets_api.delete_bucket(buckets)
                self.buckets_api.create_bucket(bucket_name=self.bucket)
        else:
            self.buckets_api.create_bucket(bucket_name=self.bucket)

    def transform_time(self, t):
        return t

    def record(self, measurement, tags, fields, time=None):
        from influxdb_client import Point

        if time is None:
            time = self.now()
        time = self.transform_time(time)

        p = Point(measurement)
        p = p.time(self.time_offset + int(time * 1e9))
        for k, v in tags.items():
            p = p.tag(k, v)
        for k, v in fields.items():
            p = p.field(k, v)

        self.write_api.write(bucket=self.bucket, record=p)

    def flush(self):
        self.write_api.flush()

    def close(self):
        self.write_api.close()
        self.influx_client.close()