import random
import math


class RoundedAmount:
    def __init__(self, min, max):
        self.min = min
        self.max = max

    def getAmount(self):
        min = int(self.min)
        max = int(self.max)
        range = max - min
        
        tentative_step_size = self.__round_up_to_power_of_ten(range)
        
        # i.e. 10, 100, 1000
        power_of_ten = self.__get_step_size(tentative_step_size, range)

        num_digits_power_of_ten = self.__number_of_digits(power_of_ten)

        start = min
        if (power_of_ten > 1):
            start = self.__get_starting_value(min, num_digits_power_of_ten)
        
        result = random.randrange(start, max + 1, power_of_ten)
        return float(result)

    
    def __get_step_size(self, step_size, range):
        slots = range // step_size
        if (slots >= 7 and slots <= 30):
            return step_size
        if (slots < 7):
            new_step_size = step_size // 10
            if new_step_size == 0:
                return new_step_size
            return self.__get_step_size(new_step_size, range)
        return self.__get_step_size(step_size * 10, range)


    def __round_up_to_power_of_ten(self, num):
        exp = math.ceil(math.log10(num))
        return 10 ** exp


    def __number_of_digits(self, num):
        digits = int(math.log10(num)) + 1
        return digits

    
    def __get_starting_value(self, min, num_digits_stepsize):
        value = round(min, num_digits_stepsize * -1)
        if value < min:
            value += 10 ** (num_digits_stepsize - 1)
        return value
        
