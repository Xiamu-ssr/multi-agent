#!/usr/bin/env python
from random import randint

from pydantic import BaseModel

from crewai.flow import Flow, listen, start

from zero_flow_state_mgt.persistent_counter_flow import run as run_persistent_counter_flow


def kickoff():
    run_persistent_counter_flow()

def run():
    kickoff()

if __name__ == "__main__":
    run()
