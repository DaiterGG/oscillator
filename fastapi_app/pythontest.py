def compress_numbers(nums):
    if not nums:
        return []

    result = [nums[0]]

    for number in nums[1:]:
        if number != result[-1]:
            result.append(number)

    return result


def test_empty_array(self):
    self.assertEqual(
        compress_numbers([]),
        []
    )

def test_single_element(self):
    self.assertEqual(
        compress_numbers([5]),
        [5]
    )

def test_removes_duplicates(self):
    self.assertEqual(
        compress_numbers([1, 1, 2, 2, 3]),
        [1, 2, 3]
    )

def test_preserves_duplicates(self):
    self.assertEqual(
        compress_numbers([0, 0, 1, 1, 0]),
        [0, 1, 0]
    )


def test_negative_numbers(self):
    self.assertEqual(
        compress_numbers([-2, -2, -1, 0, 0, -1]),
        [-2, -1, 0, -1]
    )
