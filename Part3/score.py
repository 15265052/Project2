length_str=6250
fin=open("INPUT.bin", "rb")
fout=open("OUTPUT.bin", "rb")
count=0
for i in range(length_str):
    strin=fin.read(1)
    strout=fout.read(1)
    if strin==strout:
        count+=1
    else:
        print("error: INPUT : ",strin," OUTPUT: ", strout, "index: ", i)

print(str(count/length_str*100)+"%")