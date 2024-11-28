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
        
    def park_spot(self, agent, spot_number):
        spot = self.get(Percept("spot"), (spot_number, "free"))
        if spot:
            self.change(spot, (spot_number, spot.args[1], spot.args[2], [agent]))
            return "DONE"
        else:
            self.print(f'Cant park at spot({spot_number})')
            return "REJECT"
        
    def free_spot(self, agent):
        spot = self.get(Percept("spot", ("ID", "CITY_ZONE", "SUBSECTOR", [agent])))
        if spot:
            self.print(f'Driver {agent} is leaving spot ({spot.args[0]})')
            self.change(spot, (spot.args[0], "free"))
        else:
            self.print(f'Driver {agent} not found')

class Manager(Agent):
    def __init__(self, agent_name=None):
        super().__init__(agent_name, read_all_mail=True)
        self.add(Goal("CalculatePrices"))

    # Mocks more complex math function
    @pl(gain, Goal("CalculatePrices"))
    def calculate_prices(self, src):
        self.spots_prices = []
        for spot_id, (_, subsector_number, _) in enumerate(product(*ranges)):
            price = 10 * subsector_number + rnd.random() % 5
            self.add(Belief("price", (spot_id, price)))

        # self.add(Goal("Negotiation", ("search", "north")))

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
            case CityZones.N:
                spot = self.get(Belief("spot", ("ID", [city_zone], "SUBSECTOR", "free")))
            case CityZones.S:
                spot = self.get(Belief("spot", ("ID", [city_zone], "SUBSECTOR", "free")))
            case CityZones.E:
                spot = self.get(Belief("spot", ("ID", [city_zone], "SUBSECTOR", "free")))
            case CityZones.W:
                spot = self.get(Belief("spot", ("ID", [city_zone], "SUBSECTOR", "free")))
        if spot:
            self.add(Goal('SendSpot', (spot, agent)), instant=True)
        return None
            
            

    @pl(gain, Goal("SendSpot", ("SPOT", "AGENT")))
    def send_spot(self, src, send_spot):
        spot, agent = send_spot
        self.print(f"Sending spot({spot}) to {agent}")
        self.send(agent, achieve,Goal("park",("Parking", spot)))
        pass

class Driver(Agent):
    def __init__(self, agent_name=None):
        super().__init__(agent_name)
        self.heading = list(CityZones)[rnd.randrange(len(CityZones.__members__))]
        self.send("Manager", achieve, Goal("Negotiation", ("search", self.heading)))


if __name__ == '__main__':
    parking = Parking()
    manager = Manager()
    driver = Driver()

    Admin().connect_to(manager, parking)
    Admin().connect_to(driver, parking)

    Admin().start_system()

    Admin().stop_all_agents()    