from rpy2 import robjects
from rpy2.interactive import process_revents
from rpy2.robjects import Formula
from rpy2.robjects.packages import importr, data
import rpy2.robjects.lib.ggplot2 as ggplot2
from rpy2.robjects.lib import grdevices

try:
    process_revents.start()
except:
    pass

base = importr('base')
datasets = importr('datasets')

mtcars = data(datasets).fetch('mtcars')['mtcars']

plot = ggplot2.ggplot(mtcars)
plot += ggplot2.aes_string(x='wt', y='mpg', col='factor(cyl)')
plot += ggplot2.geom_point()
plot += ggplot2.ggtitle('Scatter plot with categories')

with grdevices.render_to_bytesio(grdevices.svg) as svg:
    plot.plot()
process_revents.stop()

svg.getvalue() 
