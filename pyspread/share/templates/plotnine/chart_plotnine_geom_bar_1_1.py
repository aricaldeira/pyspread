from plotnine import aes, geom_bar, ggplot, theme_classic
from plotnine.data import mpg

plot = ggplot(mpg)
plot += geom_bar(aes(x='class', fill='drv'))
plot += theme_classic()

plot.draw()
