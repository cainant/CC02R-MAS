from maspy import *
import random as rnd
from time import sleep
from itertools import product
from enum import Enum

city_zones = ['N', 'S', 'E', 'W']
CityZones = Enum('CityZones', city_zones)
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
        self.print(f'({agent.str_name}) is parking ({spot.args[0]})')
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
        self.deals = 0
        self.failed_deals = 0
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
        # self.print(f'Negotiating {act}')
        match act:
            case "search":
                self.add(Goal("SearchSpot", (execute, src)))
                pass
            case "accept":
               spot, agent = execute
               self.deals += 1
               self.action('Parking').park_spot(agent, spot)
               self.add(Goal("CalculatePrices"))
               pass
            case "reject":
                self.failed_deals += 1
                pass
            case "offer":
                spot, agent, price = execute
                self.add(Goal("CheckOffer", (spot, [agent], price)))
                pass
        
    @pl(gain, Goal("SearchSpot", ("CITY_ZONE", "AGENT")))
    def search_spot(self, src, search_spot):
        city_zone, agent = search_spot
        self.print(f'Searching spot in ({city_zone}) for ({agent})')
        spot = None
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
            
            
    @pl(gain, Goal("OfferSpot", ("SPOT", "AGENT")))
    def offer_spot(self, src, offer_spot):
        spot, agent = offer_spot
        self.print(f'Offering spot ({spot}) for ({agent})')
        spot_id = spot.args[0]
        price = self.prices_list[spot_id]
        self.send(agent, achieve, Goal("Negotiation", ("offer", (price, spot))))

    # Mocks function to check offer price
    @pl(gain, Goal("CheckOffer", ("SPOT", "AGENT", "PRICE")))
    def check_offer(self, src, offer):
        spot, agent, price = offer
        self.print(f'Checking offer from ({agent})')
        if(rnd.choice([True, False])):
            self.send(agent[0].str_name, tell, Belief("Parked"))
            execute = (spot, agent[0])
            self.add(Goal("Negotiation", ("accept", execute)), instant=True)
        else:
            self.send(agent[0].str_name, tell, Belief("NotParked"))
            self.add(Goal("Negotiation", ("reject", agent)))

class Driver(Agent):
    def __init__(self, agent_name=None):
        super().__init__(agent_name)
        self.times_parked = 0
        self.add(Belief('NotParked'))
        

    @pl(gain, Goal("Negotiation", ("ACT", "EXECUTE")))
    def negotiation(self, src, negotiation):
        act, execute = negotiation
        match act:
            case "offer":
                price, spot = execute
                self.add(Goal('CheckPrice', (price, spot)))
                

    @pl(gain, Goal('CheckPrice', ("PRICE", "SPOT")))
    def check_price(self, src, checkprice):
        price, spot = checkprice
        if(rnd.choice([True, False])):
            self.print(f'Accepting spot at ({spot})')
            execute = (spot, self, rnd.random())
            self.send('Manager', achieve, Goal("Negotiation", ("offer", execute)))
        else:
            self.print(f'Rejecting spot at ({spot})')
            self.send('Manager', achieve, Goal("Negotiation", ("reject", spot)))
            self.add(Belief('NotParked'))

    @pl(gain, Belief('Parked'))
    def parked(self, src):
        self.times_parked += 1
        if (self.times_parked == 2):
            self.stop_cycle()
            return
        self.print('Parking')
        sleep(3)
        self.print('Leaving spot')
        self.action('Parking').free_spot(self)
        self.add(Belief('NotParked'))

    @pl(gain, Belief('NotParked'))
    def not_parked(self, src):
        self.print('Looking for spot')
        self.heading = CityZones[rnd.choice(city_zones)]
        self.send("Manager", achieve, Goal("Negotiation", ("search", [self.heading])))
    

if __name__ == '__main__':
    parking = Parking()
    manager = Manager()
    driver = [Driver() for _ in range(10)]

    Admin().connect_to(manager, parking)
    Admin().connect_to(driver, parking)

    Admin().start_system()

    Admin().stop_all_agents()    