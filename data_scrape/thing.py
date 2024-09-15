arr = []
for i in range(97, 123):
    for j in range(97, 123):
        for k in range(97, 123):
            arr.append(chr(i)+chr(j)+chr(k))
print(arr)