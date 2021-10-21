length_str=10000
fin=open("INPUT.txt", "r")
fout=open("OUTPUT.txt", "r")
count=0
for i in range(length_str):
    strin=fin.read(1)
    strout=fout.read(1)
    if strin==strout:
        count+=1
    else:
        print("error: INPUT : ",strin," OUTPUT: ", strout, "index: ", i)

print(str(count/10000*100)+"%")