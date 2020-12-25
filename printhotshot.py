import hotshot, hotshot.stats


stats = hotshot.stats.load("j.prof")
stats.strip_dirs()
stats.sort_stats('time', 'calls')
stats.print_stats()

