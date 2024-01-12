import pstats
p = pstats.Stats('profile_stats')
p.sort_stats('cumulative').print_stats(10)  # Adjust number to show more or fewer lines