import random
from datetime import datetime

class NumberGeneration:  # PEP 8 convention: Class names should be PascalCase

    def __init__(self):
        self.generated_asn_ids = []
        self.generated_lpn_ids = None
        self.bol_nbr = None
        self.pro_nbr = None
        self.trailer_nbr = None
        self.seal_nbr = None
        # --- Counters moved to instance level ---
        self.lpn_unique_counter = 0
        self.misc_unique_counter = 0
        self.generated_fr_order_ids = []

    def asn_number_generation(self, num_of_asn_to_generate: int, envn: str, initial: str) -> list:
        if not isinstance(num_of_asn_to_generate, int) or num_of_asn_to_generate <= 0:
            print("Warning: Number of ASN is zero or invalid. No ASN IDs will be generated for this data row.")
            return []

        # Clear previous results for new generation batch
        self.generated_asn_ids = []
        timestamp = datetime.now().strftime('%m%d')
        for i in range(num_of_asn_to_generate):
            # Using a wider random range and the loop index for better uniqueness
            unique_part = f"{random.randint(100, 999)}{i}"
            id_ = f"{initial}ASN{timestamp}{envn.upper()}{unique_part}"  # 'id' is a built-in, better to use 'id_'
            self.generated_asn_ids.append(id_)
        return self.generated_asn_ids

    def lpn_number_generation(self, envn: str):
        if not envn:  # More pythonic check for None or empty string
            print("Warning: Environment not provided. Cannot generate LPN.")
            return None

        # Generate the LPN and then increment the counter for the next call {envn.upper()}
        self.generated_lpn_ids = (
            f'00081{datetime.today().strftime('%m%d%Y')}'
            f'{random.randint(10000, 99999)}{self.lpn_unique_counter:02d}'
        )

        self.lpn_unique_counter += 1
        return self.generated_lpn_ids

    def misc_nbr(self, envn: str):
        if not envn:  # More pythonic check
            print("Warning: Environment not provided. Cannot generate misc numbers.")
            return None, None, None, None  # Return a tuple of Nones

        # Corrected f-string and use of the instance counter
        self.misc_unique_counter = f'{random.randint(10, 99)}'
        base_seq = (
            f"{envn.upper()}{datetime.today().strftime('%m%d%y')}"
            f"{self.misc_unique_counter}"
        )

        # Assign to instance attributes
        self.bol_nbr = f'BOL{base_seq}'
        self.pro_nbr = f'PRO{base_seq}'
        self.trailer_nbr = f'TRL{base_seq}'
        self.seal_nbr = f'SL{base_seq}'

        return self.bol_nbr, self.pro_nbr, self.trailer_nbr, self.seal_nbr

    def order_number_generation(self, num_of_order_to_generate: int, envn: str, initial: str):
        if not isinstance(num_of_order_to_generate, int) or num_of_order_to_generate <= 0:
            print("Warning: Number of ASN is zero or invalid. No ASN IDs will be generated for this data row.")
            return []

        # Clear previous results for new generation batch
        self.generated_order_ids = []
        timestamp = datetime.now().strftime('%m%d')
        for i in range(num_of_order_to_generate):
            # Using a wider random range and the loop index for better uniqueness
            unique_part = f"{random.randint(100, 999)}{i}"
            id_ = f"{initial}{timestamp}{unique_part}"
            self.generated_order_ids.append(id_)
        return self.generated_order_ids

    def fr_order_number_generation(self, num_of_order_to_generate: int, envn: str, initial: str):
        if not isinstance(num_of_order_to_generate, int) or num_of_order_to_generate <= 0:
            print("Warning: Number of ASN is zero or invalid. No ASN IDs will be generated for this data row.")
            return []

        # Clear previous results for new generation batch
        self.generated_fr_order_ids = []
        timestamp = datetime.now().strftime('%m%d')
        for i in range(num_of_order_to_generate):
            # Using a wider random range and the loop index for better uniqueness
            unique_part = f"{random.randint(100, 999)}{i}"
            id_ = f"{initial}{timestamp}{unique_part}"
            self.generated_fr_order_ids.append(id_)
        return self.generated_fr_order_ids

    def purchase_order_number(self):
        self.generated_po_ids = (
            f'PO{datetime.today().strftime('%m%d')}{random.randint(1000, 9999)}')

        return self.generated_po_ids


    def create_shipment_number(self):
        self.generated_shipment_ids = (
            f"VGS{datetime.today().strftime('%m%d%y')}{random.randint(100, 999)}"
        )

        return self.generated_shipment_ids

    def loading_group_number(self):
        self.generated_loading_group_ids = (
            f"VL{datetime.today().strftime('%m%d%y')}{random.randint(100, 999)}"
        )
        return self.generated_loading_group_ids

if __name__ == '__main__':
    # # To execute this class to check on in the later stage.
    number_generation = NumberGeneration()
    # asn = number_generation.asn_number_generation(2, 'dev')
    # print(asn)
    lpn = number_generation.lpn_number_generation(envn='qa')
    print(lpn)
    # bol, pro, trailer, seal = number_generation.misc_nbr('dev')
    # print(bol, pro, trailer, seal)
    # order = number_generation.order_number_generation(2, 'QA', 'VG')
    # print(order)
    # shipment = number_generation.create_shipment_number()
    # print(shipment)
    # loading = number_generation.loading_group_number()
    # print(loading)

