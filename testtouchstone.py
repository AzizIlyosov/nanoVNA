from controllers.Touchstone import Touchstone
t= Touchstone('/home/aziz/Desktop/nanoVNA/test/data/attenuator-0643_MA.s2p')
t.load()
print(t.s11data)