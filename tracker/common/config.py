from dcplib.config import Config


class TrackerInfraConfig(Config):

    def __init__(self, *args, **kwargs):
        super().__init__(component_name='tracker', secret_name='infra', **kwargs)
