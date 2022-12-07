from rpy2 import robjects
from rpy2.interactive import process_revents
from rpy2.robjects import Formula
from rpy2.robjects.vectors import IntVector, FloatVector
from rpy2.robjects.packages import importr, data
import rpy2.robjects.lib.ggplot2 as ggplot2
from rpy2.robjects.lib import grdevices

try:
    process_revents.start()
except:
    pass

base = importr('base')
stats = importr('stats')

rnorm = stats.rnorm
dataf_rnorm = robjects.DataFrame({'value': rnorm(300, mean=0) + rnorm(100, mean=3),
                                  'other_value': rnorm(300, mean=0) + rnorm(100, mean=3),
                                  'mean': IntVector([0, ]*300 + [3, ] * 100)})

plot = ggplot2.ggplot(dataf_rnorm)
plot += ggplot2.aes_string(x='value', y='other_value')
plot += ggplot2.geom_point(alpha = 0.3)
plot += ggplot2.geom_density2d(ggplot2.aes_string(col = '..level..'))
plot += ggplot2.ggtitle('Scatter plot with kernel density estimate')

with grdevices.render_to_bytesio(grdevices.svg) as svg:
    plot.plot()
process_revents.stop()

svg.getvalue() 
