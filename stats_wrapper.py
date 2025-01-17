import numpy as np
from gymnasium import Env, spaces
from map_data import map_locations
from events import filtered_event_names

event_flags_start = 0xD747
event_flags_end = 0xD887
MAP_N_ADDRESS = 0xD35E

class StatsWrapper(Env):
    def __init__(self, env):
        self.env = env
        self.action_space = env.action_space
        self.observation_space = env.observation_space
        self.max_steps = env.max_steps

    def reset(self):
        obs, info = self.env.reset()
        self.init_stats_fields(obs["events"])
        return obs, info

    def step(self, action):
        obs, reward, done, truncated, info = self.env.step(action)
        self.update_stats(obs["events"])
        if done or truncated:
            info = self.get_info()
        return obs, reward, done, truncated, info

    def render(self):
        return self.env.render()
    
    def init_stats_fields(self, event_obs):
        self.party_size = 1
        self.total_heal = 0
        self.died_count = 0
        self.party_levels = np.asarray([-1 for _ in range(6)])
        self.events_sum = 0
        self.max_opponent_level = 0
        self.seen_coords = 0
        self.current_location = self.env.read_m(MAP_N_ADDRESS)
        self.location_first_visit_steps = {loc: -1 for loc in map_locations.keys()}
        self.location_frequency = {loc: 0 for loc in map_locations.keys()}
        self.location_steps_spent = {loc: 0 for loc in map_locations.keys()}
        self.current_events = event_obs
        self.events_steps = {name: -1 for name in filtered_event_names}
        # Pokedex caught species (or species in party, depending on what's easier)
        # Move usage (count pp consumed)
        # Poke center usage (count number of times used to heal, maybe per poke center)
        # Item usage (antidote, potion, pokeball is quite obsvious)

    def update_stats(self, event_obs):
        self.party_size = self.env.party_size
        self.seen_coords = len(self.env.seen_coords)
        self.max_opponent_level = self.env.max_opponent_level
        self.update_location_stats()
        self.update_event_stats(event_obs)

    def update_location_stats(self):
        new_location = self.env.read_m(MAP_N_ADDRESS)
        # Steps needed to reach this location
        if self.location_first_visit_steps[new_location] == -1:
            self.location_first_visit_steps[new_location] = self.env.step_count
        # Number of times this location was visited
        if new_location != self.current_location:
            self.location_frequency[new_location] += 1
            self.current_location = new_location
        # Number of steps that were spent in this location
        elif new_location == self.current_location:
            self.location_steps_spent[new_location] += 1

    def update_event_stats(self, event_obs):
        # check if self.current_events is equal to event_obs
        # if not, find the index that is different and update the steps
        comparison = self.current_events == event_obs
        if np.all(comparison):
            return
        changed_ids = np.where(comparison == False)[0]
        for i in changed_ids:
            self.events_steps[filtered_event_names[i]] = self.env.step_count
        self.current_events = event_obs

    def get_info(self):
        info = {
                "party_size": self.party_size,
                "total_heal": self.total_heal,
                "died_count": self.died_count,
                "party_levels": self.party_levels,
                "events_sum": self.events_sum,
                "max_opponent_level": self.max_opponent_level,
                "seen_coords": self.seen_coords,
                "location_first_visit_steps": self.location_first_visit_steps,
                "location_frequency": self.location_frequency,
                "location_steps_spent": self.location_steps_spent,
                "events_steps": self.events_steps
            }
        return info