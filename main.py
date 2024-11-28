from maspy import *
import random as rnd
from time import sleep
from itertools import product
from enum import Enum

CityZones = Enum('CityZones', ['N', 'S', 'E', 'W'])
number_of_subsectors = 3
number_of_spots = 10

ranges = [CityZones, range(number_of_subsectors), range(number_of_spots)]

class Parking(Environment):
    def __init__(self, env_name: str | None = 'Parking'):
        super().__init__(env_name, True)
        self.print(f'Starting parking')
        for spot_id, (city_zone, subsector_number, _) in enumerate(product(*ranges)):
            self.create(Percept("spot", (spot_id, [city_zone], subsector_number + 1, "free")))
        
    def park_spot(self, agent, spot):
        self.change(spot, (spot.args[0], spot.args[1], spot.args[2], [agent]))
        
    def free_spot(self, agent):
        spot = self.get(Percept("spot", ("ID", "CITY_ZONE", "SUBSECTOR", [agent])))
        if spot:
            self.print(f'({agent.str_name}) is leaving spot ({spot.args[0]})')
            self.change(spot, (spot.args[0], spot.args[1], spot.args[2], "free"))
        else:
            self.print(f'Driver {agent} not found')

class Manager(Agent):
    def __init__(self, agent_name=None):
        super().__init__(agent_name, read_all_mail=True)
        self.prices_list = []
        self.add(Goal("CalculatePrices"))

    # Mocks more complex math function
    @pl(gain, Goal("CalculatePrices"))
    def calculate_prices(self, src):
        for _, (_, subsector_number, _) in enumerate(product(*ranges)):
            price = 10 * (subsector_number + 1) + rnd.random() % 5
            self.prices_list.append(price)

    @pl(gain, Goal("Negotiation", ("ACT", "EXECUTE")))
    def negotiation(self, src, negotiation):
        act, execute = negotiation
        match act:
            case "search":
                self.add(Goal("SearchSpot", (execute, src)))
                pass
            case "accept":
                pass
                # allocate spot 
            case "reject":
                pass
                # :(
            case "offer":
                pass
                # offer slot
        
    @pl(gain, Goal("SearchSpot", ("CITY_ZONE", "AGENT")))
    def search_spot(self, src, search_spot):
        city_zone, agent = search_spot
        match city_zone:
            case [CityZones.N]:
                spot = self.get(Belief("spot", ("ID", city_zone, "SUBSECTOR", "free")))
            case [CityZones.S]:
                spot = self.get(Belief("spot", ("ID", city_zone, "SUBSECTOR", "free")))
            case [CityZones.E]:
                spot = self.get(Belief("spot", ("ID", city_zone, "SUBSECTOR", "free")))
            case [CityZones.W]:
                spot = self.get(Belief("spot", ("ID", city_zone, "SUBSECTOR", "free")))
        if spot:
            self.add(Goal('OfferSpot', (spot, agent)), instant=True)
        return None
            
            
    @pl(gain, Goal("OfferSpot", ("SPOT", "AGENT")))
    def offer_spot(self, src, offer_spot):
        spot, agent = offer_spot
        spot_id = spot.args[0]
        price = self.prices_list[spot_id]
        self.send(agent, achieve, Goal("Negotiation", ("offer", (price, spot))))

class Driver(Agent):
    def __init__(self, agent_name=None):
        super().__init__(agent_name)
        self.heading = list(CityZones)[rnd.randrange(len(CityZones.__members__))]
        self.send("Manager", achieve, Goal("Negotiation", ("search", [self.heading])))

    @pl(gain, Goal("Negotiation", ("ACT", "EXECUTE")))
    def negotiation(self, src, negotiation):
        act, execute = negotiation
        match act:
            case "offer":
                price, spot = execute
                # check price for spot
                if ('parking'):
                    self.action('Parking').park_spot(self, spot)

        self.stop_cycle()

    def stop_cycle(self, log_flag=False) -> None:
        self.action('Parking').free_spot(self)
        super().stop_cycle(log_flag)

if __name__ == '__main__':
    parking = Parking()
    manager = Manager()
    driver = Driver()

    Admin().connect_to(manager, parking)
    Admin().connect_to(driver, parking)

    Admin().start_system()

    Admin().stop_all_agents()    


'''
TODO:
- Driver loop for parking and freeing spot
- Manager must recalculate all prices after driver parking and freeing spot
'''