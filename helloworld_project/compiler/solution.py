def sol_0(y: str) -> bool:
    x = int(y)
    if x < 0 or (x > 0 and x % 10 == 0):
        return str(False)
    sum = 0
    while x > sum:
        sum = (sum * 10) + x % 10
        x = x // 10
    return str((sum // 10 == x or sum == x))

def sol_1(y: str):
    nums = list(map(int, y.split()))
    k=0
    l = len(nums)
    for x in range (0,l):
            if(x ==0 or nums[x]!=nums[x-1]):
                nums[k]=nums[x]
                k+=1
    return str(k)