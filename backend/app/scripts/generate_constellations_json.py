import json
from pathlib import Path

constellations = {
        "Andromeda": {
            "description": "Named after the princess in Greek mythology, chained to a rock to be sacrificed to a sea monster.",
            "myth": "Daughter of Cepheus and Cassiopeia, rescued by Perseus.",
            "discoverer": "Ancient Greeks",
            "year": "300 BCE",
            "brightest_star": "Alpheratz",
            "major_stars": [
                "Alpheratz",
                "Mirach",
                "Almach"
            ]
        },
        "Antlia": {
            "description": "A faint constellation representing an air pump.",
            "myth": "Named by Nicolas Louis de Lacaille in the 18th century.",
            "discoverer": "Lacaille",
            "year": "1751",
            "brightest_star": "Alpha Antliae",
            "major_stars": [
                "Alpha Antliae"
            ]
        },
        "Apus": {
            "description": "Depicts a bird-of-paradise.",
            "myth": "Created by Petrus Plancius from explorers' observations.",
            "discoverer": "Petrus Plancius",
            "year": "1597",
            "brightest_star": "Alpha Apodis",
            "major_stars": [
                "Alpha Apodis",
                "Gamma Apodis"
            ]
        },
        "Aquarius": {
            "description": "One of the oldest constellations; represents the water bearer.",
            "myth": "Associated with Ganymede, cupbearer to the gods.",
            "discoverer": "Babylonians",
            "year": "1000 BCE",
            "brightest_star": "Sadalsuud",
            "major_stars": [
                "Sadalsuud",
                "Sadalmelik"
            ]
        },
        "Aquila": {
            "description": "Represents an eagle that carried Zeus's thunderbolts.",
            "myth": "Symbolizes the eagle of Zeus.",
            "discoverer": "Ancient Greeks",
            "year": "300 BCE",
            "brightest_star": "Altair",
            "major_stars": [
                "Altair",
                "Tarazed",
                "Alshain"
            ]
        },
        "Ara": {
            "description": "Represents the altar where the gods formed an alliance.",
            "myth": "Used by the gods to swear allegiance before fighting the Titans.",
            "discoverer": "Ancient Greeks",
            "year": "200 BCE",
            "brightest_star": "Beta Arae",
            "major_stars": [
                "Beta Arae",
                "Gamma Arae"
            ]
        },
        "Aries": {
            "description": "Symbolizes the ram that saved Phrixus and Helle in Greek myth.",
            "myth": "The ram with the Golden Fleece.",
            "discoverer": "Ancient Greeks",
            "year": "300 BCE",
            "brightest_star": "Hamal",
            "major_stars": [
                "Hamal",
                "Sheratan",
                "Mesarthim"
            ]
        },
        "Auriga": {
            "description": "Represents a charioteer.",
            "myth": "Sometimes linked with Erichthonius of Athens.",
            "discoverer": "Ancient Greeks",
            "year": "300 BCE",
            "brightest_star": "Capella",
            "major_stars": [
                "Capella",
                "Menkalinan"
            ]
        },
        "Boötes": {
            "description": "Depicts a herdsman, often associated with Arcas.",
            "myth": "Son of Zeus and Callisto.",
            "discoverer": "Ancient Greeks",
            "year": "300 BCE",
            "brightest_star": "Arcturus",
            "major_stars": [
                "Arcturus",
                "Izar",
                "Seginus"
            ]
        },
        "Caelum": {
            "description": "Represents a sculptor’s chisel.",
            "myth": "No myth; created by Lacaille.",
            "discoverer": "Lacaille",
            "year": "1751",
            "brightest_star": "Alpha Caeli",
            "major_stars": [
                "Alpha Caeli"
            ]
        },
        "Camelopardalis": {
            "description": "A faint northern constellation representing a giraffe.",
            "myth": "Created in the 17th century.",
            "discoverer": "Petrus Plancius",
            "year": "1612",
            "brightest_star": "Beta Camelopardalis",
            "major_stars": [
                "Beta Camelopardalis"
            ]
        },
        "Cancer": {
            "description": "One of the zodiac constellations, representing a crab.",
            "myth": "Sent by Hera to distract Hercules.",
            "discoverer": "Ancient Greeks",
            "year": "300 BCE",
            "brightest_star": "Altarf",
            "major_stars": [
                "Altarf",
                "Acubens"
            ]
        },
        "Canes Venatici": {
            "description": "Represents the hunting dogs of Boötes.",
            "myth": "Created by Hevelius.",
            "discoverer": "Johannes Hevelius",
            "year": "1687",
            "brightest_star": "Cor Caroli",
            "major_stars": [
                "Cor Caroli",
                "Chara"
            ]
        },
        "Canis Major": {
            "description": "Represents the greater dog of Orion.",
            "myth": "One of Orion's hunting dogs.",
            "discoverer": "Ancient Greeks",
            "year": "300 BCE",
            "brightest_star": "Sirius",
            "major_stars": [
                "Sirius",
                "Mirzam",
                "Adhara"
            ]
        },
        "Canis Minor": {
            "description": "The lesser dog of Orion.",
            "myth": "Usually represented as Maera.",
            "discoverer": "Ancient Greeks",
            "year": "300 BCE",
            "brightest_star": "Procyon",
            "major_stars": [
                "Procyon",
                "Gomeisa"
            ]
        },
        "Capricornus": {
            "description": "A zodiac constellation representing a sea-goat.",
            "myth": "Linked to the god Pan.",
            "discoverer": "Babylonians",
            "year": "1000 BCE",
            "brightest_star": "Deneb Algedi",
            "major_stars": [
                "Deneb Algedi",
                "Dabih"
            ]
        },
        "Carina": {
            "description": "Part of the former Argo Navis constellation.",
            "myth": "The keel of the Argo, the ship of Jason and the Argonauts.",
            "discoverer": "Ancient Greeks",
            "year": "300 BCE",
            "brightest_star": "Canopus",
            "major_stars": [
                "Canopus",
                "Miaplacidus"
            ]
        },
        "Cassiopeia": {
            "description": "Represents a vain queen in Greek mythology.",
            "myth": "Mother of Andromeda.",
            "discoverer": "Ancient Greeks",
            "year": "300 BCE",
            "brightest_star": "Schedar",
            "major_stars": [
                "Schedar",
                "Caph",
                "Ruchbah"
            ]
        },
        "Centaurus": {
            "description": "A bright southern constellation.",
            "myth": "Represents Chiron the centaur.",
            "discoverer": "Ancient Greeks",
            "year": "300 BCE",
            "brightest_star": "Alpha Centauri",
            "major_stars": [
                "Alpha Centauri",
                "Beta Centauri"
            ]
        },
        "Cepheus": {
            "description": "Represents the king of Ethiopia.",
            "myth": "Father of Andromeda.",
            "discoverer": "Ancient Greeks",
            "year": "300 BCE",
            "brightest_star": "Alderamin",
            "major_stars": [
                "Alderamin",
                "Alfirk"
            ]
        },
        "Cetus": {
            "description": "Represents a sea monster in Greek mythology.",
            "myth": "Sent by Poseidon to devour Andromeda.",
            "discoverer": "Ancient Greeks",
            "year": "300 BCE",
            "brightest_star": "Deneb Kaitos",
            "major_stars": [
                "Deneb Kaitos",
                "Menkar"
            ]
        },
        "Chamaeleon": {
            "description": "A faint southern constellation representing a chameleon.",
            "myth": "Created by Plancius in the 16th century.",
            "discoverer": "Petrus Plancius",
            "year": "1597",
            "brightest_star": "Alpha Chamaeleontis",
            "major_stars": [
                "Alpha Chamaeleontis"
            ]
        },
        "Circinus": {
            "description": "Represents a compass.",
            "myth": "Created by Lacaille in the 18th century.",
            "discoverer": "Nicolas Louis de Lacaille",
            "year": "1751",
            "brightest_star": "Alpha Circini",
            "major_stars": [
                "Alpha Circini"
            ]
        },
        "Columba": {
            "description": "Represents a dove.",
            "myth": "Created by Plancius in the 16th century.",
            "discoverer": "Petrus Plancius",
            "year": "1597",
            "brightest_star": "Phact",
            "major_stars": [
                "Phact",
                "Wazn"
            ]
        },
        "Coma Berenices": {
            "description": "Represents the hair of Berenice II of Egypt.",
            "myth": "Berenice sacrificed her hair for her husband's safe return.",
            "discoverer": "Ancient Greeks",
            "year": "300 BCE",
            "brightest_star": "Beta Comae Berenices",
            "major_stars": [
                "Beta Comae Berenices",
                "Gamma Comae Berenices"
            ]
        },
        "Corona Australis": {
            "description": "Represents a southern crown.",
            "myth": "Associated with the wedding crown of Achelous and Deianira.",
            "discoverer": "Ancient Greeks",
            "year": "300 BCE",
            "brightest_star": "Alpha Coronae Australis",
            "major_stars": [
                "Alpha Coronae Australis",
                "Beta Coronae Australis"
            ]
        },
        "Corona Borealis": {
            "description": "Represents a northern crown.",
            "myth": "Associated with Ariadne's crown.",
            "discoverer": "Ancient Greeks",
            "year": "300 BCE",
            "brightest_star": "Alphecca",
            "major_stars": [
                "Alphecca",
                "Beta Coronae Borealis"
            ]
        },
        "Corvus": {
            "description": "Represents a crow in Greek mythology.",
            "myth": "Associated with Apollo and the story of the crow's punishment.",
            "discoverer": "Ancient Greeks",
            "year": "300 BCE",
            "brightest_star": "Gienah",
            "major_stars": [
                "Gienah",
                "Kraz"
            ]
        },
        "Crater": {
            "description": "Represents a cup in Greek mythology.",
            "myth": "Associated with Apollo and the crow.",
            "discoverer": "Ancient Greeks",
            "year": "300 BCE",
            "brightest_star": "Delta Crateris",
            "major_stars": [
                "Delta Crateris",
                "Gamma Crateris"
            ]
        },
        "Crux": {
            "description": "The Southern Cross, smallest constellation.",
            "myth": "Used in navigation.",
            "discoverer": "European navigators",
            "year": "16th century",
            "brightest_star": "Acrux",
            "major_stars": [
                "Acrux",
                "Becrux",
                "Gacrux"
            ]
        },
        "Cygnus": {
            "description": "The swan; one of the most recognizable constellations.",
            "myth": "Linked to Zeus and the story of Leda.",
            "discoverer": "Ancient Greeks",
            "year": "300 BCE",
            "brightest_star": "Deneb",
            "major_stars": [
                "Deneb",
                "Albireo",
                "Sadr"
            ]
        },
        "Delphinus": {
            "description": "A dolphin; a small but ancient constellation.",
            "myth": "Dolphin sent by Poseidon to find Amphitrite.",
            "discoverer": "Ancient Greeks",
            "year": "300 BCE",
            "brightest_star": "Rotanev",
            "major_stars": [
                "Rotanev",
                "Sualocin"
            ]
        },
        "Dorado": {
            "description": "A swordfish or dolphinfish.",
            "myth": "No myth; navigational origin.",
            "discoverer": "Dutch explorers",
            "year": "1597",
            "brightest_star": "Alpha Doradus",
            "major_stars": [
                "Alpha Doradus"
            ]
        },
        "Draco": {
            "description": "A dragon curled around the north celestial pole.",
            "myth": "Slain by Hercules.",
            "discoverer": "Ancient Greeks",
            "year": "300 BCE",
            "brightest_star": "Eltanin",
            "major_stars": [
                "Eltanin",
                "Thuban"
            ]
        },
        "Equuleus": {
            "description": "A little horse, or foal.",
            "myth": "Often associated with Pegasus.",
            "discoverer": "Ancient Greeks",
            "year": "300 BCE",
            "brightest_star": "Kitalpha",
            "major_stars": [
                "Kitalpha"
            ]
        },
        "Eridanus": {
            "description": "A river flowing through the sky.",
            "myth": "Associated with the River Po or Nile.",
            "discoverer": "Ancient Greeks",
            "year": "300 BCE",
            "brightest_star": "Achernar",
            "major_stars": [
                "Achernar",
                "Cursa"
            ]
        },
        "Fornax": {
            "description": "The furnace; a modern constellation.",
            "myth": "No myth.",
            "discoverer": "Lacaille",
            "year": "1751",
            "brightest_star": "Alpha Fornacis",
            "major_stars": [
                "Alpha Fornacis"
            ]
        },
        "Gemini": {
            "description": "The twins, Castor and Pollux.",
            "myth": "Twin brothers turned into stars by Zeus.",
            "discoverer": "Ancient Greeks",
            "year": "300 BCE",
            "brightest_star": "Pollux",
            "major_stars": [
                "Castor",
                "Pollux",
                "Alhena"
            ]
        },
        "Grus": {
            "description": "A crane, created by early navigators.",
            "myth": "No myth; southern constellation.",
            "discoverer": "Petrus Plancius",
            "year": "1598",
            "brightest_star": "Alnair",
            "major_stars": [
                "Alnair"
            ]
        },
        "Hercules": {
            "description": "The mythological hero.",
            "myth": "Celebrates the Greek hero Heracles.",
            "discoverer": "Ancient Greeks",
            "year": "300 BCE",
            "brightest_star": "Kornephoros",
            "major_stars": [
                "Kornephoros",
                "Rasalgethi"
            ]
        },
        "Horologium": {
            "description": "A clock; named by Lacaille.",
            "myth": "No mythology.",
            "discoverer": "Lacaille",
            "year": "1751",
            "brightest_star": "Alpha Horologii",
            "major_stars": [
                "Alpha Horologii"
            ]
        },
        "Hydra": {
            "description": "The water serpent, largest constellation.",
            "myth": "Slain by Hercules.",
            "discoverer": "Ancient Greeks",
            "year": "300 BCE",
            "brightest_star": "Alphard",
            "major_stars": [
                "Alphard",
                "Hydri"
            ]
        },
        "Hydrus": {
            "description": "The male water snake.",
            "myth": "Not related to Hydra.",
            "discoverer": "Petrus Plancius",
            "year": "1597",
            "brightest_star": "Beta Hydri",
            "major_stars": [
                "Beta Hydri"
            ]
        },
        "Indus": {
            "description": "Represents an Indian, created by Plancius.",
            "myth": "No specific myth; navigational constellation.",
            "discoverer": "Petrus Plancius",
            "year": "1597",
            "brightest_star": "Alpha Indi",
            "major_stars": [
                "Alpha Indi"
            ]
        },
        "Lacerta": {
            "description": "Lacerta is a faint northern constellation introduced in the 17th century. Its name is Latin for 'lizard'.",
            "myth": "It was not associated with any mythological creature, serving instead as a space-filler between more prominent constellations.",
            "discoverer": "Johannes Hevelius",
            "year": "1687",
            "brightest_star": "Alpha Lacertae",
            "major_stars": [
                "Alpha Lacertae",
                "Beta Lacertae",
                "EV Lacertae"
            ]
        },
        "Leo": {
            "description": "One of the most ancient and recognizable zodiac constellations, Leo depicts a lion.",
            "myth": "Represents the Nemean Lion, slain by Hercules as one of his twelve labors.",
            "discoverer": "Ancient Babylonians and Greeks",
            "year": "2000 BCE",
            "brightest_star": "Regulus",
            "major_stars": [
                "Regulus",
                "Denebola",
                "Algieba",
                "Zosma",
                "Chort"
            ]
        },
        "Leo Minor": {
            "description": "A small and faint northern constellation named the 'Lesser Lion'.",
            "myth": "Not associated with any classical mythology; introduced to fill a gap in the star maps.",
            "discoverer": "Johannes Hevelius",
            "year": "1687",
            "brightest_star": "46 Leonis Minoris",
            "major_stars": [
                "46 LMi",
                "21 LMi",
                "Beta LMi"
            ]
        },
        "Lepus": {
            "description": "Located just south of Orion, Lepus represents a hare in the night sky.",
            "myth": "Often considered prey for Orion the hunter, though specific myths are sparse.",
            "discoverer": "Ancient Greeks",
            "year": "300 BCE",
            "brightest_star": "Arneb",
            "major_stars": [
                "Arneb",
                "Nihal",
                "Gamma Leporis"
            ]
        },
        "Libra": {
            "description": "A zodiac constellation symbolizing a pair of scales — the only inanimate object among zodiac signs.",
            "myth": "Linked with Themis or Astraea, goddesses of justice.",
            "discoverer": "Babylonians (as 'Balance of Heaven')",
            "year": "1000 BCE",
            "brightest_star": "Zubenelgenubi",
            "major_stars": [
                "Zubenelgenubi",
                "Zubeneschamali",
                "Brachium"
            ]
        },
        "Lupus": {
            "description": "A southern constellation traditionally depicted as a wolf.",
            "myth": "In Greek and Roman depictions, it was an animal being sacrificed by Centaurus.",
            "discoverer": "Ancient Greeks",
            "year": "300 BCE",
            "brightest_star": "Alpha Lupi",
            "major_stars": [
                "Alpha Lupi",
                "Beta Lupi",
                "Gamma Lupi"
            ]
        },
        "Lynx": {
            "description": "A faint northern constellation named after the lynx, known for its keen eyesight.",
            "myth": "No direct mythology; the name suggests it can only be seen by those with sharp eyes.",
            "discoverer": "Johannes Hevelius",
            "year": "1687",
            "brightest_star": "Alpha Lyncis",
            "major_stars": [
                "Alpha Lyncis",
                "38 Lyncis"
            ]
        },
        "Lyra": {
            "description": "Lyra is a small constellation representing the lyre of Orpheus, a musical instrument from Greek mythology.",
            "myth": "Orpheus played the lyre so beautifully that he charmed gods and mortals alike.",
            "discoverer": "Ancient Greeks",
            "year": "300 BCE",
            "brightest_star": "Vega",
            "major_stars": [
                "Vega",
                "Sheliak",
                "Sulafat"
            ]
        },
        "Mensa": {
            "description": "A southern constellation named after Table Mountain in South Africa.",
            "myth": "It has no mythological significance and was introduced for navigation.",
            "discoverer": "Nicolas Louis de Lacaille",
            "year": "1751",
            "brightest_star": "Alpha Mensae",
            "major_stars": [
                "Alpha Mensae"
            ]
        },
        "Microscopium": {
            "description": "A modern constellation representing a microscope.",
            "myth": "No mythology; symbolizes scientific advancement.",
            "discoverer": "Nicolas Louis de Lacaille",
            "year": "1751",
            "brightest_star": "Gamma Microscopii",
            "major_stars": [
                "Gamma Microscopii"
            ]
        },
        "Monoceros": {
            "description": "Depicts a unicorn, located between Orion and Hydra.",
            "myth": "Inspired by medieval depictions of unicorns, symbolizing purity.",
            "discoverer": "Petrus Plancius",
            "year": "1612",
            "brightest_star": "Alpha Monocerotis",
            "major_stars": [
                "Alpha Monocerotis",
                "Beta Monocerotis",
                "Epsilon Monocerotis"
            ]
        },
        "Musca": {
            "description": "A southern constellation representing a fly.",
            "myth": "No classical mythology; created during the age of exploration.",
            "discoverer": "Petrus Plancius",
            "year": "1597",
            "brightest_star": "Alpha Muscae",
            "major_stars": [
                "Alpha Muscae"
            ]
        },
        "Norma": {
            "description": "A modern constellation representing a carpenter’s square or level.",
            "myth": "Symbolic of precision and measurement; no mythology.",
            "discoverer": "Nicolas Louis de Lacaille",
            "year": "1751",
            "brightest_star": "Gamma2 Normae",
            "major_stars": [
                "Gamma2 Normae",
                "Epsilon Normae"
            ]
        },
        "Octans": {
            "description": "Home to the south celestial pole, Octans represents a navigational octant.",
            "myth": "Has no mythological basis.",
            "discoverer": "Nicolas Louis de Lacaille",
            "year": "1752",
            "brightest_star": "Nu Octantis",
            "major_stars": [
                "Nu Octantis",
                "Beta Octantis"
            ]
        },
        "Ophiuchus": {
            "description": "The Serpent Bearer, often considered the '13th zodiac sign'.",
            "myth": "Associated with Asclepius, the god of medicine who learned to bring the dead back to life.",
            "discoverer": "Ancient Greeks",
            "year": "300 BCE",
            "brightest_star": "Rasalhague",
            "major_stars": [
                "Rasalhague",
                "Sabik",
                "Yed Prior"
            ]
        },
        "Orion": {
            "description": "Perhaps the most iconic constellation, Orion represents a giant hunter.",
            "myth": "Killed by a scorpion, he was placed in the sky by Zeus.",
            "discoverer": "Ancient Greeks",
            "year": "300 BCE",
            "brightest_star": "Rigel",
            "major_stars": [
                "Rigel",
                "Betelgeuse",
                "Bellatrix",
                "Saiph",
                "Mintaka",
                "Alnilam",
                "Alnitak"
            ]
        },
        "Pavo": {
            "description": "Pavo is a southern constellation representing a peacock, a bird known for its colorful plumage.",
            "myth": "Often associated with Hera's sacred bird in Greek mythology, though it was introduced during European exploration.",
            "discoverer": "Petrus Plancius",
            "year": "1597",
            "brightest_star": "Peacock (Alpha Pavonis)",
            "major_stars": [
                "Alpha Pavonis",
                "Beta Pavonis",
                "Gamma Pavonis"
            ]
        },
        "Pegasus": {
            "description": "Pegasus represents the winged horse from Greek mythology.",
            "myth": "Born from the blood of Medusa, Pegasus served heroes and was placed in the stars by Zeus.",
            "discoverer": "Ancient Greeks",
            "year": "300 BCE",
            "brightest_star": "Enif",
            "major_stars": [
                "Enif",
                "Markab",
                "Scheat",
                "Algenib"
            ]
        },
        "Perseus": {
            "description": "A prominent constellation that honors the Greek hero Perseus.",
            "myth": "Perseus slew Medusa and rescued Andromeda, later married her.",
            "discoverer": "Ancient Greeks",
            "year": "300 BCE",
            "brightest_star": "Mirfak",
            "major_stars": [
                "Mirfak",
                "Algol",
                "Atik"
            ]
        },
        "Phoenix": {
            "description": "Phoenix is a southern constellation named after the mythical bird that regenerates from its ashes.",
            "myth": "Symbolizes immortality and rebirth, based on legends from Ancient Egypt and Greece.",
            "discoverer": "Petrus Plancius",
            "year": "1597",
            "brightest_star": "Ankaa",
            "major_stars": [
                "Ankaa",
                "Beta Phoenicis"
            ]
        },
        "Pictor": {
            "description": "Pictor represents a painter's easel and is one of the modern constellations.",
            "myth": "Has no mythological associations; introduced to honor the arts and sciences.",
            "discoverer": "Nicolas Louis de Lacaille",
            "year": "1751",
            "brightest_star": "Alpha Pictoris",
            "major_stars": [
                "Alpha Pictoris"
            ]
        },
        "Pisces": {
            "description": "Pisces, the Fishes, is a zodiac constellation symbolizing two fish swimming in opposite directions.",
            "myth": "According to Greek myth, Aphrodite and her son Eros transformed into fish to escape the monster Typhon.",
            "discoverer": "Babylonians (refined by Greeks)",
            "year": "1000 BCE",
            "brightest_star": "Eta Piscium",
            "major_stars": [
                "Eta Piscium",
                "Alrescha"
            ]
        },
        "Piscis Austrinus": {
            "description": "The Southern Fish, a small constellation just south of Aquarius.",
            "myth": "Associated with the myth of the fish that saved the Egyptian goddess Isis.",
            "discoverer": "Ancient Babylonians",
            "year": "2000 BCE",
            "brightest_star": "Fomalhaut",
            "major_stars": [
                "Fomalhaut",
                "Beta PsA"
            ]
        },
        "Puppis": {
            "description": "Puppis represents the stern (rear) of the ship Argo Navis from Greek mythology.",
            "myth": "Originally part of a giant constellation Argo, which represented the ship of Jason and the Argonauts.",
            "discoverer": "Ancient Greeks",
            "year": "300 BCE",
            "brightest_star": "Naos",
            "major_stars": [
                "Naos",
                "Tureis",
                "Asmidiske"
            ]
        },
        "Pyxis": {
            "description": "A small southern constellation representing a mariner’s compass.",
            "myth": "Symbolizes navigation and discovery, not derived from mythology.",
            "discoverer": "Nicolas Louis de Lacaille",
            "year": "1752",
            "brightest_star": "Alpha Pyxidis",
            "major_stars": [
                "Alpha Pyxidis"
            ]
        },
        "Reticulum": {
            "description": "Reticulum, the Net, is a southern constellation symbolizing a reticle used in telescopes.",
            "myth": "Has no mythology; honors advancements in astronomy and instrumentation.",
            "discoverer": "Nicolas Louis de Lacaille",
            "year": "1751",
            "brightest_star": "Alpha Reticuli",
            "major_stars": [
                "Alpha Reticuli"
            ]
        },
        "Sagitta": {
            "description": "Sagitta means 'arrow' in Latin and is one of the smallest constellations in the night sky.",
            "myth": "Possibly represents the arrow used by Hercules or Apollo.",
            "discoverer": "Ancient Greeks",
            "year": "300 BCE",
            "brightest_star": "Gamma Sagittae",
            "major_stars": [
                "Gamma Sagittae",
                "Delta Sagittae"
            ]
        },
        "Sagittarius": {
            "description": "A prominent zodiac constellation representing a centaur archer.",
            "myth": "Linked to Chiron or another wise centaur; protector and archer.",
            "discoverer": "Babylonians and Greeks",
            "year": "1000 BCE",
            "brightest_star": "Kaus Australis",
            "major_stars": [
                "Kaus Australis",
                "Nunki",
                "Ascella"
            ]
        },
        "Scorpius": {
            "description": "A striking zodiac constellation shaped like a scorpion.",
            "myth": "Sent by Gaia or Apollo to kill Orion. The two were placed on opposite sides of the sky.",
            "discoverer": "Ancient Babylonians",
            "year": "1100 BCE",
            "brightest_star": "Antares",
            "major_stars": [
                "Antares",
                "Shaula",
                "Sargas"
            ]
        },
        "Sculptor": {
            "description": "Sculptor honors the craft of sculpture and creativity.",
            "myth": "No mythology; part of Lacaille’s scientific constellations.",
            "discoverer": "Nicolas Louis de Lacaille",
            "year": "1751",
            "brightest_star": "Alpha Sculptoris",
            "major_stars": [
                "Alpha Sculptoris"
            ]
        },
        "Scutum": {
            "description": "Latin for 'shield', Scutum was created to honor a Polish king.",
            "myth": "No myth; honors King John III Sobieski of Poland.",
            "discoverer": "Johannes Hevelius",
            "year": "1684",
            "brightest_star": "Alpha Scuti",
            "major_stars": [
                "Alpha Scuti",
                "Beta Scuti"
            ]
        },
        "Serpens": {
            "description": "Serpens is unique as it’s split into two parts: Serpens Caput (head) and Serpens Cauda (tail), separated by Ophiuchus.",
            "myth": "Represents the serpent held by Asclepius, god of healing.",
            "discoverer": "Ancient Greeks",
            "year": "300 BCE",
            "brightest_star": "Unukalhai",
            "major_stars": [
                "Unukalhai",
                "Eta Serpentis",
                "Mu Serpentis"
            ]
        },
        "Sextans": {
            "description": "Named after the astronomical sextant, Sextans is a modern constellation.",
            "myth": "No mythology; symbolizes observational tools.",
            "discoverer": "Johannes Hevelius",
            "year": "1687",
            "brightest_star": "Alpha Sextantis",
            "major_stars": [
                "Alpha Sextantis"
            ]
        },
        "Taurus": {
            "description": "A zodiac constellation symbolizing a bull.",
            "myth": "Zeus transformed into a bull to abduct Europa.",
            "discoverer": "Babylonians and Greeks",
            "year": "1000 BCE",
            "brightest_star": "Aldebaran",
            "major_stars": [
                "Aldebaran",
                "Elnath",
                "Alcyone (Pleiades)"
            ]
        },
        "Telescopium": {
            "description": "Telescopium pays tribute to the telescope, a revolutionary astronomical instrument.",
            "myth": "No mythological origins.",
            "discoverer": "Nicolas Louis de Lacaille",
            "year": "1751",
            "brightest_star": "Alpha Telescopii",
            "major_stars": [
                "Alpha Telescopii"
            ]
        },
        "Triangulum": {
            "description": "A small, triangular constellation with ancient roots.",
            "myth": "Sometimes linked to the Nile Delta or the Greek letter Delta.",
            "discoverer": "Ancient Greeks",
            "year": "300 BCE",
            "brightest_star": "Beta Trianguli",
            "major_stars": [
                "Beta Trianguli",
                "Gamma Trianguli"
            ]
        },
        "Triangulum Australe": {
            "description": "The southern triangle; a small but bright constellation.",
            "myth": "No classical mythology; represents mathematical harmony.",
            "discoverer": "Petrus Plancius",
            "year": "1589",
            "brightest_star": "Atria",
            "major_stars": [
                "Atria",
                "Beta TrA"
            ]
        },
        "Tucana": {
            "description": "Represents a toucan, one of several southern birds added to maps during the Age of Exploration.",
            "myth": "No mythological background; symbolizes biodiversity.",
            "discoverer": "Petrus Plancius",
            "year": "1598",
            "brightest_star": "Alpha Tucanae",
            "major_stars": [
                "Alpha Tucanae"
            ]
        },
        "Ursa Major": {
            "description": "The Great Bear; one of the oldest known constellations, famous for the Big Dipper asterism.",
            "myth": "Linked to Callisto, transformed into a bear and placed in the sky by Zeus.",
            "discoverer": "Ancient Greeks",
            "year": "300 BCE",
            "brightest_star": "Alioth",
            "major_stars": [
                "Dubhe",
                "Merak",
                "Alioth",
                "Mizar",
                "Alkaid"
            ]
        },
        "Ursa Minor": {
            "description": "The Little Bear, home to Polaris, the North Star.",
            "myth": "Often identified with Arcas, son of Callisto.",
            "discoverer": "Ancient Greeks",
            "year": "300 BCE",
            "brightest_star": "Polaris",
            "major_stars": [
                "Polaris",
                "Kochab",
                "Pherkad"
            ]
        },
        "Vela": {
            "description": "Represents the sails of the ship Argo Navis.",
            "myth": "Part of the great ship used by Jason and the Argonauts.",
            "discoverer": "Ancient Greeks",
            "year": "300 BCE",
            "brightest_star": "Suhail",
            "major_stars": [
                "Suhail",
                "Alsephina",
                "Markeb"
            ]
        },
        "Virgo": {
            "description": "The second largest constellation, Virgo represents a maiden holding wheat.",
            "myth": "Often identified with Demeter or Astraea, goddess of justice.",
            "discoverer": "Ancient Greeks",
            "year": "300 BCE",
            "brightest_star": "Spica",
            "major_stars": [
                "Spica",
                "Vindemiatrix"
            ]
        },
        "Volans": {
            "description": "Symbolizes a flying fish, added during the age of maritime exploration.",
            "myth": "No myth; celebrates unique southern hemisphere fauna.",
            "discoverer": "Petrus Plancius",
            "year": "1597",
            "brightest_star": "Beta Volantis",
            "major_stars": [
                "Beta Volantis",
                "Gamma Volantis"
            ]
        },
        "Vulpecula": {
            "description": "Latin for 'little fox', Vulpecula is a faint northern constellation.",
            "myth": "Created to honor lesser-known animals in the sky.",
            "discoverer": "Johannes Hevelius",
            "year": "1687",
            "brightest_star": "Anser",
            "major_stars": [
                "Anser",
                "23 Vulpeculae"
            ]
        }
    }

output_path = Path("data/constellations.json")
output_path.parent.mkdir(parents=True, exist_ok=True)

with output_path.open("w", encoding="utf-8") as f:
    json.dump(constellations, f, indent=2, ensure_ascii=False)

print(f"✅ Constellations JSON written to {output_path.resolve()}")