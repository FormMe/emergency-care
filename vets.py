import json


class Vet:
    def __init__(self, name, city, district, address, phones, website):
        self.name = name
        self.city = city
        self.district = district
        self.address = address
        self.phones = phones
        self.website = website
    
    def __str__(self):
        msg = f"*{self.name}*\n"
        msg += "📍Адрес: " + self.address + "\n"
        msg += "📞Телефон:\n"
        for phone in self.phones:
            msg += f"\t\t•\t{phone}\n"
        msg += f"[🌐Веб-сайт](self.website)"
        return msg
            

class Vets:
    def __init__(self, path):
        with open(path) as f:
            vets = json.load(f)
        self.vets = self.read_vets(vets)

    def read_vets(self, vets):
        return [Vet(**vet) for vet in vets]
    
    def get_districts(self, city=None):
        districts = []
        for vet in self.vets:
            if city is None:
                districts.append(vet.district)
                continue
            if vet.city == city:
                districts.append(vet.district)
        return set(districts)

    def get_vets(self, city=None, district=None):
        return [vet for vet in self.vets if vet.city == city and vet.district == district]




