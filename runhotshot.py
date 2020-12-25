import hotshot, hotshot.stats, test.pystone
import j
prof = hotshot.Profile("j.prof")
prof.runcall(j.__main__)
prof.close()
