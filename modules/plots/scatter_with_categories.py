import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import numpy as np

from collections import OrderedDict
import itertools
import matplotlib.patches as patches

from modules.utils import *
	
class scatterWithCategories(object):


	def __init__(self,plotter,dfClass,figure,categoricalColumns=[],numericalColumns=[], colorMap = 'Blues'):#data,n_cols,n_categories,colnames,catnames,figure,size,color):
	
		self.grouped_data = None
		self.grouped_keys = None
		
		self.unique_values = OrderedDict() 	
		self.axes = OrderedDict() 
		self.label_axes = OrderedDict() 
		self.axes_combs = OrderedDict()
		self.subsets_and_scatter = OrderedDict() 
		self.sizeStatsAndColorChanges = OrderedDict() 
		
		self.categoricalColorDefinedByUser = dict()
		self.colorMapDict = dict()	
		self.colorMap = colorMap
		
		self.dataID = dfClass.currentDataFile 
		self.data = dfClass.get_current_data_by_column_list(categoricalColumns+numericalColumns)
		self.dfClass = dfClass
		self.data.dropna(inplace=True)
		self.plotter = plotter
		
		self.numericalColumns = numericalColumns
		self.categoricalColumns = categoricalColumns
		self.numbNumericalColumns = len(numericalColumns)
		self.numbCaetgoricalColumns = len(categoricalColumns)
		self.size = self.plotter.sizeScatterPoints 
		self.color = self.plotter.colorScatterPoints
		self.alpha = self.plotter.alphaScatterPoints
		self.figure = figure
		
		plt.figure(self.figure.number)
		
		self.get_unique_values() 
				
		self.group_data()
		
		n_rows,n_cols = self.calculate_grid_subplot()
		self.prepare_plotting(n_rows,n_cols) 
		
	
	def replot(self):
		'''
		'''
		self.grouped_keys = self.grouped_data.groups.keys()
		plt.figure(self.figure.number)
		n_rows,n_cols = self.calculate_grid_subplot()
		self.prepare_plotting(n_rows,n_cols) 
		
		
	def prepare_plotting(self,n_rows,n_cols):
		'''
		Function to plot different groups ...
		'''	
		
		self.figure.subplots_adjust(wspace=0, hspace=0, right=0.96)

		titles = list(self.unique_values[self.categoricalColumns[0]][0])
		if self.numbNumericalColumns == 1:
			# Plots the numeric column against index 
			min_y = self.data[self.numericalColumns[0]].min()
			max_y = self.data[self.numericalColumns[0]].max()
			
			
		elif self.numbNumericalColumns == 2:
			# Plot numeric column against numeric column if there are two columns
			min_x, max_x = self.data[self.numericalColumns[0]].min(), self.data[self.numericalColumns[0]].max()
			min_y, max_y = self.data[self.numericalColumns[1]].min(), self.data[self.numericalColumns[1]].max()
			xlim = 	(min_x - 0.1*min_x, max_x + 0.1*max_x )	
		
		ylim = (min_y - 0.1*min_y, max_y + 0.1*max_y )			
			
			
		if self.numbCaetgoricalColumns  > 1:
		
			y_labels = list(self.unique_values[self.categoricalColumns[1]][0])
			
		if self.numbCaetgoricalColumns == 3:
		
			levels_3,n_levels_3 = self.unique_values[self.categoricalColumns[2]]
			outer = gridspec.GridSpec(n_levels_3, 1, hspace=0.01)
			gs_saved = dict() 
			for n in range(n_levels_3):			
				gs_ = gridspec.GridSpecFromSubplotSpec(n_rows, n_cols, subplot_spec = outer[n], hspace=0.0)
				gs_saved[n] = gs_
			
		for i,comb in enumerate(self.all_combinations):
			
			if comb in self.grouped_keys:
				group = self.grouped_data.get_group(comb)

				if self.numbNumericalColumns == 1:
					n_data_group = len(group.index)
					x_ = range(0,n_data_group) 
					y_ = group[self.numericalColumns[0]]	
				
				else:			
					x_ = group[self.numericalColumns[0]]
					y_ = group[self.numericalColumns[1]]
				

			else:
				### '''This is to plot nothing if category is not in data'''
				group = None
				x_ = []
				y_ = []

			
			pos = self.get_position_of_subplot(comb) 
			if self.numbCaetgoricalColumns < 3:
				n = 0
				ax_ = plt.subplot2grid((n_rows, n_cols), pos)
				
			else:
				n = levels_3.index(comb[2])
				ax_ = self.create_ax_from_grid_spec(comb,pos,n, gs_saved)	
				
			scat = self.plotter.add_scatter_collection(ax_,x_,y_, color = self.color, 
								size=self.size, alpha=self.alpha,picker=True)
			self.annotate_axes(ax_)
														
			#ax_.plot(x_,y_,'o',color = self.color,ms = np.sqrt(self.size),
					#markeredgecolor ='black',markeredgewidth =0.3)#,linestyle=None)					
			if ax_.is_last_row() == False and self.numbCaetgoricalColumns < 3 and self.numbNumericalColumns > 1:
			
				ax_.set_xticklabels([])
				 
			elif self.numbCaetgoricalColumns == 3 and self.numbNumericalColumns > 1:
				if n != n_levels_3-1:
					ax_.set_xticklabels([])
				else:
					if ax_.is_last_row() == False:
						ax_.set_xticklabels([])
			else:
				ax_.set_xticklabels([])
			if ax_.is_last_col():			
				ax_.yaxis.tick_right()
			else:
				ax_.set_yticklabels([])	
			ax_.set_ylim(ylim)
			if self.numbNumericalColumns == 2:
				ax_.set_xlim(xlim)
			self.axes[i] = ax_
			self.axes_combs[comb] = [ax_,scat]
		self.add_labels_to_figure()	

	def annotate_axes(self,ax_):
		'''
		'''
		if ax_.is_first_col():
			if self.numbNumericalColumns == 2:
					text_ = self.numericalColumns[1]
			else:
					text_ = self.numericalColumns[0]
			self.plotter.add_annotationLabel_to_plot(ax_,
													text=text_,
													rotation = 90)
		if ax_.is_last_col():		
			if self.numbNumericalColumns == 2:
					text_ = self.numericalColumns[0]
			else:
					text_ = 'Index' 
			self.plotter.add_annotationLabel_to_plot(ax_,
														text=text_,
														position = 'bottomright')

	def save_color_and_size_changes(self,funcName,column):
		'''
		'''
		self.sizeStatsAndColorChanges[funcName] = column
	

	def remove_color_and_size_changes(self,which='color'):
		'''
		Removes color and size changes from all subplots.
		'''
		for ax,_ in self.axes_combs.values():
			axCollections = ax.collections 
			for coll in axCollections:
				if which == 'size' and hasattr(coll,'set_sizes'):
					coll.set_sizes([self.size])
				elif which == 'color' and hasattr(coll,'set_color'):
					coll.set_facecolor(self.color)
					
	def change_size_by_numerical_column(self,numericColumn):
		'''
		'''	
		## update data if missing columns 
		self.data = self.dfClass.join_missing_columns_to_other_df(self.data,id=self.dataID,
																  definedColumnsList=[numericColumn])	
		
		scaledData = scale_data_between_0_and_1(self.data[numericColumn])
		scaledData = (scaledData+0.3)*100
		self.data['size'] = scaledData
		self.adjust_size()
		self.save_color_and_size_changes('change_size_by_numerical_column',numericColumn)			
	
	
	def change_size_by_categorical_columns(self,categoricalColumn):
		'''
		
		'''
		self.data = self.dfClass.join_missing_columns_to_other_df(self.data,id=self.dataID,
																  definedColumnsList=[categoricalColumn])
		
		uniqueCategories = self.data[categoricalColumn].unique()
		numberOfUuniqueCategories = uniqueCategories.size

		scaleSizes = np.linspace(0.3,1,num=numberOfUuniqueCategories,endpoint=True)
		sizeMap = dict(zip(uniqueCategories, scaleSizes))
		
		sizeMap = replace_key_in_dict('-',sizeMap,0.1)
		self.data['size'] = self.data[categoricalColumn].map(sizeMap)
		self.data['size'] = (self.data['size'])*100 
		self.adjust_size()		
		self.save_color_and_size_changes('change_size_by_categorical_column',categoricalColumn)
	
	
	def adjust_size(self):
		'''
		'''
		self.group_data()	
		for comb in self.all_combinations:
			if comb in self.grouped_keys:
				subset = self.grouped_data.get_group(comb)
				ax,_ = self.axes_combs[comb]
				axCollection = ax.collections
				axCollection[0].set_sizes(subset['size'])


	def adjust_color(self):
		'''
		'''
		self.group_data()	
		for comb in self.all_combinations:
			if comb in self.grouped_keys:
				subset = self.grouped_data.get_group(comb)
				ax,_ = self.axes_combs[comb]
				axCollection = ax.collections
				axCollection[0].set_facecolor(subset['size'])
		
			
	def change_color_by_numerical_column(self,numericColumn):
		'''
		accepts a numeric column from the dataCollection class. numeric is added using 
		the index ensuring that correct dots get the right color. 
		'''
		cmap = get_max_colors_from_pallete(self.colorMap)
			
		## update data if missing columns 
		self.data = self.dfClass.join_missing_columns_to_other_df(self.data,id=self.dataID,
																  definedColumnsList=[numericColumn])	
		scaledData = scale_data_between_0_and_1(self.data[numericColumn]) 
		self.data['color']= [col_c(cmap(value)) for value in scaledData]
		self.group_data()
		for comb in self.all_combinations:
			if comb in self.grouped_keys:
				subset = self.grouped_data.get_group(comb)
				ax,_ = self.axes_combs[comb]
				axCollection = ax.collections
				axCollection[0].set_facecolor(subset['color'].values)		
		self.save_color_and_size_changes('change_color_by_numerical_column',numericColumn)
		
			
	def change_color_by_categorical_columns(self,categoricalColumn, updateColor = True):
		'''
		'''
		self.colorMapDict,layerMapDict, self.rawColorMapDict = get_color_category_dict(self.dfClass,categoricalColumn,
												self.colorMap, self.categoricalColorDefinedByUser,
												self.color)
		## update data if missing columns 
		self.data = self.dfClass.join_missing_columns_to_other_df(self.data,id=self.dataID,
																  definedColumnsList=categoricalColumn)			
		
		
		if len(categoricalColumn) == 1:
			self.data.loc[:,'color'] = self.data[categoricalColumn[0]].map(self.colorMapDict)
		else:
			self.data.loc[:,'color'] = self.data[categoricalColumn].apply(tuple,axis=1).map(self.colorMapDict)
				
		if updateColor == False:
			self.data.loc[:,'layer'] = self.data['color'].map(layerMapDict)		
			self.data.sort_values('layer', ascending = True, inplace=True)	
		self.group_data()				
						
		for comb in self.all_combinations:
			if comb in self.grouped_keys:
				subset = self.grouped_data.get_group(comb)
				ax,_ = self.axes_combs[comb]
				if updateColor:
					axCollection = ax.collections
					axCollection[0].set_facecolor(subset['color'].values)
				else:
					# get the previous size
					size = ax.collections[0].get_sizes()
					## delete the previous collection
					## needed because otherwise we cannot change the layer 
					## changing the layer is actually not needed if the number of numerical
					## columns is 1 because they points cannot really overly unless
					## we have a lot of data points, therefore we keep it like this. 
					ax.collections[0].remove()
					if self.numbNumericalColumns == 1:
						n_data_group = len(subset.index)
						x_ = range(0,n_data_group) 
						y_ = subset[self.numericalColumns[0]]								
					else:			
						x_ = subset[self.numericalColumns[0]]
						y_ = subset[self.numericalColumns[1]]				
														
					self.plotter.add_scatter_collection(ax,x=x_,
											y = y_, size=size,
											color = subset['color'].values, picker = True)		
		self.save_color_and_size_changes('change_color_by_categorical_columns',
													categoricalColumn)	
	def get_current_colorMapDict(self):
		'''
		'''
		return self.colorMapDict
			
	def update_colorMap(self,newColorMap=None):
		'''
		'''
		if newColorMap is not None:
			self.colorMap = newColorMap
		for functionName,column in self.sizeStatsAndColorChanges.items(): 
			getattr(self,functionName)(column)  
				
	def change_nan_color(self,newColor):
		'''
		'''
		for ax in self.plotter.get_axes_of_figure():
			for coll in ax.collections:
				coll.set_facecolor(newColor)
		self.color = newColor

	def change_size(self,size):
		'''
		'''
		for ax in self.plotter.get_axes_of_figure:
			for coll in ax.collections:
				coll.set_sizes([size])
		self.color = size		
	
	def create_ax_from_grid_spec(self,comb,pos, n, gs_saved):
		'''
		Gets the appropiate axis from selected gridspec- In principle we have gridspecs in one big gridspec, 
		this allows hspacing between certain categories on y axis.
		'''
		
		gs_ = gs_saved[n]	
		ax = plt.subplot(gs_[pos])
		return ax
				
	
	def add_labels_to_figure(self):
		'''
		Adds labels to figure  - still ugly 
		To DO. make this function cleaner. 
		'''
		
		levels_1,n_levels_1 = self.unique_values[self.categoricalColumns[0]]
		
		if self.numbCaetgoricalColumns == 1:
			bottomSpace = 0.5
			
		else:
			bottomSpace = 0.14
		
		self.figure.subplots_adjust(left=0.15, bottom= bottomSpace) 
		
		ax_top = self.figure.add_axes([0.15,0.89,0.81,0.15])
		ax_top.set_ylim((0,4))
		ax_top.axis('off') 
		width_for_rect = 1/n_levels_1
		kwargs_rectangle_main = dict(edgecolor='black',clip_on=False,linewidth=0.1,fill=True)
		kwargs_rectangle = dict(edgecolor='black',clip_on=False,linewidth=0.1,fill=False)
		ax_top.add_patch(patches.Rectangle((0,1),1,1,**kwargs_rectangle_main))
		ax_top.text(0.5, 1.5 , s = self.categoricalColumns[0], horizontalalignment='center',verticalalignment = 'center',color="white")
		
		for n,level in enumerate(levels_1):
			
			x = 0 + n * width_for_rect
			y = 0
			width = width_for_rect
			height = 1 
			ax_top.add_patch(patches.Rectangle((x,y),width,height,**kwargs_rectangle))
			ax_top.text(x + width/2 , height/2, s = level, 
				horizontalalignment='center',verticalalignment = 'center')
		self.label_axes['top_limits'] = [ax_top.get_xlim(),ax_top.get_ylim()]	
		self.label_axes['top'] = ax_top
		
		if self.numbCaetgoricalColumns > 1:
		
			ax_left = self.figure.add_axes([0.02,0.14,0.1,0.74])
			ax_left.axis('off')
			ax_left.set_xlim((0,4)) 
			ax_left.add_patch(patches.Rectangle((2,0),1,1,**kwargs_rectangle_main))
			ax_left.text(2.5, 0.5 , s = self.categoricalColumns[1], verticalalignment='center', 
				rotation=90,horizontalalignment='center',color="white")
			levels_2,n_levels_2 = self.unique_values[self.categoricalColumns[1]]
			if self.numbCaetgoricalColumns == 3:
				levels_3,n_levels_3 = self.unique_values[self.categoricalColumns[2]]
				n_levels_2 = n_levels_2 * n_levels_3
				levels_2 = levels_2 * n_levels_3
				
			height_for_rect = 1/n_levels_2
			for n,level in enumerate(levels_2):
				
				y = 1 - (n+1) * height_for_rect
				x = 3
				width = 1
				height = height_for_rect 
				
				ax_left.add_patch(patches.Rectangle((x,y),width,height,**kwargs_rectangle))
				ax_left.text(x + width/2 , y + height/2, s = level, verticalalignment='center', 
					rotation=90,horizontalalignment='center')
			if self.numbCaetgoricalColumns == 3:
			
				
				ax_left.add_patch(patches.Rectangle((0,0),1,1,**kwargs_rectangle_main))
				ax_left.text(0.5, 0.5 , s = self.categoricalColumns[2], verticalalignment='center', rotation=90,
									horizontalalignment='center',color="white")
				height_for_rect = 1/n_levels_3
				for n,level in enumerate(levels_3):
					y = 1 - (n+1) * height_for_rect
					x = 1
					height = height_for_rect
					ax_left.add_patch(patches.Rectangle((x,y),width,height,**kwargs_rectangle))					
					ax_left.text(x + width/2 , y + height/2, s = level, verticalalignment='center', rotation=90,horizontalalignment='center')
			
			self.label_axes['left'] = ax_left
		if self.numbCaetgoricalColumns > 1:
			self.inmutableAxes = [self.label_axes['top'],self.label_axes['left']]
		else:
			self.inmutableAxes = [self.label_axes['top']]
			
		

		
			
	def get_position_of_subplot(self, comb):
		'''
		Returns the position of the specific combination of levels in categorical columns. 
		Seems a bit complicated but is needed if a certain combination is missing.
		'''
		levels_1, n_levels_1 = self.unique_values[self.categoricalColumns[0]]
		if self.numbCaetgoricalColumns == 1:
			row = 0
			col = levels_1.index(comb)
		else:
			levels_2,n_levels_2 = self.unique_values[self.categoricalColumns[1]]
			col = levels_1.index(comb[0])
			row = levels_2.index(comb[1])
			
			
		return (row,col)
	
	
	
	def calculate_grid_subplot(self):
		'''
		Calculates the subplots to display data
		'''
	
		## get columns of n_cat 1 
		if self.numbCaetgoricalColumns == 1:
		
			levels_1, n_levels = self.unique_values[self.categoricalColumns[0]]
			n_cols = n_levels
			n_rows = 1 
			self.all_combinations = list(levels_1)
			
		elif self.numbCaetgoricalColumns == 2:
		
			levels_1, n_levels_1 = self.unique_values[self.categoricalColumns[0]]
			n_cols = n_levels_1
			levels_2, n_levels_2 = self.unique_values[self.categoricalColumns[1]]
			n_rows = n_levels_2
			self.all_combinations = list(itertools.product(levels_1,levels_2))
				
		elif self.numbCaetgoricalColumns == 3:
		
			levels_1, n_levels_1 = self.unique_values[self.categoricalColumns[0]]
			n_cols = n_levels_1
			levels_2, n_levels_2 = self.unique_values[self.categoricalColumns[1]]
			n_rows = n_levels_2
			levels_3, n_levels_3 = self.unique_values[self.categoricalColumns[2]]
			self.all_combinations = list(itertools.product(levels_1,levels_2,levels_3))	
			
		return n_rows, n_cols	
			
	
	def get_unique_values(self):
		'''
		Determines unique vlaues in each category, that is needed to build the subplots
		'''
		for category in self.categoricalColumns:
			
			uniq_levels = self.data[category].unique()
			n_levels = uniq_levels.size
			
			self.unique_values[category] = [list(uniq_levels),n_levels]
			
		
	def group_data(self):
		'''
		Returns a pandas groupby object with grouped data on selected categories.
		'''
		
		self.grouped_data = self.data.groupby(self.categoricalColumns, sort = False) 
		self.grouped_keys = self.grouped_data.groups.keys()
		
		
		
	def __getstate__(self):
		'''
		Remove stuff that cannot be steralized by pickle
		'''
		state = self.__dict__.copy()
		for attr in ['figure','grouped_keys']:
			if attr in state: 
				del state[attr]
		return state
			#'_Plotter',		
		
		