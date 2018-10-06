import ast
import random
import copy
import operator			# to use operations as methods
from pydoc import locate #to determine type from type name
from mutpy import utils	#classes of nodes that allow to differenciate between nodes

log_name = 'log.txt'
mark_name = 'type_mark'

def controlledP(str,end="\n"):
	global log_name
	f = open(log_name,'a')
	f.write(str)
	f.write(end)
	f.close()
def clearP():
	global log_name
	f = open(log_name,'w')
	f.close()	
def nothing(*x,**X):
	pass
def controlledPrint(str,end="\n"):
	pass
def clearPrint():
	pass
def debugReportEnablement(enable):
	if enable:
		controlledPrint = controlledP
		clearPrint = clearP
	else:
		controlledPrint = nothing
		clearPrint = nothing
debugReportEnablement(False)

class MutationAnnResign(Exception):
    pass
class UnknownType():
	pass	
class IncompatibleType():
	pass	
class NotAnASTNodeType(IncompatibleType):
	pass	
class IgnorableType():
	pass


def check_for_types(left_types:set,right_types:set,operation):
	possible_types = set()
	for left_type in left_types:
		for right_type in right_types:
			if left_type == UnknownType or right_type == UnknownType:
				possible_types.add(UnknownType)
			else:
				left_dummy = left_type()
				right_dummy = right_type()
				result_dummy = UnknownType
				if operation == operator.mod or operation == operator.truediv or operation == operator.floordiv:
					if right_dummy == 0:
						right_dummy = right_type(1)
				try:
					result_dummy = operation(left_dummy,right_dummy)
				except TypeError:
					pass
				except ZeroDivisionError:
					controlledPrint("ZeroDivisionError occured while testing operations on types.")
					possible_types.add(UnknownType)
				else:
					possible_types.add(type(result_dummy))
	return possible_types

def check_for_types_with_node(left_types:set,right_types:set,node):
	op_type = type(node)
	if op_type == ast.Add:
		operationToCheck = operator.add
	elif op_type == ast.Sub:
		operationToCheck = operator.sub
	elif op_type == ast.Mult:
		operationToCheck = operator.mul
	elif op_type == ast.Div:
		operationToCheck = operator.truediv
	elif op_type == ast.Mod:
		operationToCheck = operator.mod
	elif op_type == ast.Pow:
		operationToCheck = operator.pow
	elif op_type == ast.FloorDiv:
		operationToCheck = operator.floordiv
	elif op_type == ast.Eq:
		operationToCheck = operator.eq
	elif op_type == ast.NotEq:
		operationToCheck = operator.ne
	elif op_type == ast.Gt:
		operationToCheck = operator.gt
	elif op_type == ast.Lt:
		operationToCheck = operator.lt
	elif op_type == ast.GtE:
		operationToCheck = operator.ge
	elif op_type == ast.LtE:
		operationToCheck = operator.le
	else:
		raise Exception('Unrecognised operator type {}'.format(node))
	return check_for_types(left_types,right_types,operationToCheck)
		
		
class annotationManagerDisabled():
	def __init__(self):
		pass
	def visit_check_if_mutable(self,node,visitor):
		pass
		
class annotationManager(annotationManagerDisabled):
	def __init__(self):
		global mark_name
		self.mark_name = mark_name
	
	def visit_check_if_mutable(self,node,visitor):
		name = "check_mutation_"+node.__class__.__name__
		if not hasattr(annotationManager,name):
			return
		else:
			fun = getattr(annotationManager,name)
			fun(self,node,visitor)
	
	def check_whole_mutant(self,root_node):
		checkable_nodes = {ast.Add,ast.Sub,ast.Mult,ast.Div,ast.Mod,ast.Pow,ast.FloorDiv,ast.Eq,ast.NotEq,ast.Gt,ast.Lt,ast.GtE,ast.LtE}
		class dummyVisitor():
			def __call__(self,node):
				return node
		def check_node(node):
			if type(node) in checkable_nodes:
				name = "check_mutation_"+node.__class__.__name__
				if not hasattr(annotationManager,name):
					return
				else:
					fun = getattr(annotationManager,name)
					fun(self,node,dummyVisitor())
		def recursion(node):
			check_node(node)
			for field, value in ast.iter_fields(node):
				if isinstance(value, list):
					for element in value:
						recursion(element)
				elif isinstance(value, ast.AST):
					recursion(value)
		transformer = utils.ParentNodeTransformer()
		root_node = transformer(root_node)
		recursion(root_node)
			
	def check_mutation_Add(self,node,visitor):
		if type(node.parent) == ast.BinOp:
			left = node.parent.left
			right = node.parent.right
		elif type(node.parent) == ast.AugAssign:
			left = node.parent.target
			right = node.parent.value
		else:
			return
		
		if not(hasattr(right,self.mark_name) and hasattr(left,self.mark_name)):
			return
		left_types = getattr(left,self.mark_name)
		right_types = getattr(right,self.mark_name)
		if left_types is None or right_types is None:
			return
		if isinstance(left_types,type):
			left_types = {left_types}
		if isinstance(right_types,type):
			right_types = {right_types}
		if UnknownType in left_types or UnknownType in right_types:
			return
		
		mutated_node = visitor(node)
		result_types_set = check_for_types_with_node(left_types,right_types,mutated_node)
		if len(result_types_set) == 0:
			raise MutationAnnResign				
	
	def check_mutation_Sub(self,node,visitor):
		self.check_mutation_Add(node,visitor)
	def check_mutation_Mult(self,node,visitor):
		self.check_mutation_Add(node,visitor)
	def check_mutation_Div(self,node,visitor):
		self.check_mutation_Add(node,visitor)	
	def check_mutation_Mod(self,node,visitor):
		self.check_mutation_Add(node,visitor)
	def check_mutation_Pow(self,node,visitor):
		self.check_mutation_Add(node,visitor)		
	def check_mutation_FloorDiv(self,node,visitor):
		self.check_mutation_Add(node,visitor)
	
	def check_mutation_Eq(self,node,visitor):
		return self.check_mutation_for_compare_parent(node,visitor)	
	def check_mutation_NotEq(self,node,visitor):
		return self.check_mutation_for_compare_parent(node,visitor)
	def check_mutation_Gt(self,node,visitor):
		return self.check_mutation_for_compare_parent(node,visitor)
	def check_mutation_GtE(self,node,visitor):
		return self.check_mutation_for_compare_parent(node,visitor)
	def check_mutation_Lt(self,node,visitor):
		return self.check_mutation_for_compare_parent(node,visitor)
	def check_mutation_LtE(self,node,visitor):
		return self.check_mutation_for_compare_parent(node,visitor)
	def check_mutation_for_compare_parent(self,node,visitor):
		if not type(node.parent) == ast.Compare:
			return
		node_id = id(node)
		index = 0
		searched_id = id(node.parent.ops[index])
		
		while node_id != searched_id:
			index+=1
			searched_id = id(node.parent.ops[index])

		if index == 0:
			left = node.parent.left
			right = node.parent.comparators[0]
		else:
			left = node.parent.comparators[index-1]
			right = node.parent.comparators[index]
			
		if not(hasattr(right,self.mark_name) and hasattr(left,self.mark_name)):
			return
		left_types = getattr(left,self.mark_name)
		right_types = getattr(right,self.mark_name)
		if left_types is None or right_types is None:
			return
		if isinstance(left_types,type):
			left_types = {left_types}
		if isinstance(right_types,type):
			right_types = {right_types}
		if UnknownType in left_types or UnknownType in right_types:
			return
		mutated_node = visitor(node)
		result_types_set = check_for_types_with_node(left_types,right_types,mutated_node)
		if len(result_types_set) == 0:
			raise MutationAnnResign				

class annotationMarkerDisabled():
	def __init__(self):
		pass
	def mark_ast_tree(self,node,depth=0,bypassBlock=False):
		pass
class annotationMarker(annotationMarkerDisabled):
	def __init__(self):
		self.variable_types_dictionary = {}
		self.list_of_nested_variable_types_dictionaries = []
		self.dictionary_level = 0
		
		self.return_types_dictionary = {}
		self.list_of_nested_return_types_dictionaries = []
		self.return_dictionary_level = 0
		
		self.recursion_block = False
		
		Type_tree_dict_interface.class_initialisation()
		
		global mark_name
		self.mark_name = mark_name		
		self.fill_return_values_of_build_in_functions()
		
		clearPrint()
		controlledPrint('\n******\nannotation marker\n******')
	
	def mark_ast_tree(self,node,depth=0,bypassBlock=False):
		str = ""
		for tree in self.variable_types_dictionary:
			str+=tree+self.variable_types_dictionary[tree].get_type_set().__str__()
		controlledPrint(depth*'\t'+'marking {0} dict {1}'.format(node,str))
		
		self.actions_before_recursion(node)
		for field, value in ast.iter_fields(node):
			self.action_before_field(node,field,value,depth)
			if not self.recursion_block or bypassBlock:	
				if isinstance(value, list):
					for element in value:
						self.mark_ast_tree(element,depth+1,bypassBlock)
				elif isinstance(value, ast.AST):
					self.mark_ast_tree(value,depth+1,bypassBlock)
		self.action_after_recursion(node)
		
		str = ""
		for tree in self.variable_types_dictionary:
			str+=tree+self.variable_types_dictionary[tree].get_type_set().__str__()
		controlledPrint(depth*'\t'+'End marking {0} dict {1}'.format(node,str))

	def actions_before_recursion(self,node):
		nodeType = type(node)
		if nodeType == ast.arg:	#ast.arg are only present in ast.FunctionDef
			if node.annotation is not None:
				annotation_type = self.annotation_to_type(node.annotation)
				if annotation_type is not None:
					self.set_variable_type(node,annotation_type)
				else:
					self.set_variable_type(node,UnknownType)
			else:
				self.set_variable_type(node,UnknownType)
		elif nodeType == ast.Break:
			Type_tree_dict_interface.loop_break_all(self.variable_types_dictionary)
		elif nodeType == ast.ClassDef:
			self.increase_nest_level()
		elif nodeType == ast.For:
			Type_tree_dict_interface.enter_loop_all(self.variable_types_dictionary)
			if node.target is not None:
				if type(node.target) is ast.Name:
					self.set_variable_type(node.target,UnknownType)
				elif type(node.target) is ast.Tuple:
					for el in node.target.elts:
						self.set_variable_type(el,UnknownType)
		elif nodeType == ast.FunctionDef:
			self.increase_nest_level()
		elif nodeType == ast.If:
			Type_tree_dict_interface.enter_ast_If_all(self.variable_types_dictionary)		
		elif nodeType == ast.Module:
			self.determine_return_types(node)
		elif nodeType == ast.Try:
			self.recursion_block = True
			Type_tree_dict_interface.enter_try_all(self.variable_types_dictionary)		
		elif nodeType == ast.While:
			Type_tree_dict_interface.enter_loop_all(self.variable_types_dictionary)
				
	def action_after_recursion(self,node):
		setattr(node,self.mark_name,self.determine_type(node))
		nodeType = type(node)
		if nodeType == ast.ClassDef:
			self.decrease_nest_level()
		elif nodeType == ast.FunctionDef:
			self.decrease_nest_level()
		elif nodeType == ast.If:
			Type_tree_dict_interface.exit_ast_If_all(self.variable_types_dictionary)
		elif nodeType == ast.Try:
			self.recursion_block = False
			Type_tree_dict_interface.exit_try_all(self.variable_types_dictionary)
		elif type(node) == ast.While or type(node) == ast.For :
			Type_tree_dict_interface.exit_ast_If_all(self.variable_types_dictionary)
			
	def action_before_field(self,node,field,value,depth):
		if type(node) == ast.If:
			if field == 'orelse':
				Type_tree_dict_interface.enter_orelse_all(self.variable_types_dictionary)
		elif type(node) == ast.For:
			if field == 'body':
				if hasattr(node.iter,self.mark_name) and node.target is not None:
					iterType = getattr(node.iter,self.mark_name)
					if type(iterType) == Type_tree.augumentedTypeInfo:
						if type(node.target) is ast.Name:
							setattr(node.target,self.mark_name,iterType.contentType)
							self.set_variable_type(node.target,iterType.contentType)
						elif type(node.target) is ast.Tuple:	# Nie sądzę żeby tak to działało
							for el in node.target.elts:
								setattr(el,self.mark_name,iterType.contentType)
								self.set_variable_type(el,iterType.contentType)
		elif type(node) == ast.Try:
			controlledPrint('action_before_field_Try_'+field)
			self.action_before_field_Try(node,field,value,depth)
	
	def action_before_field_Try(self,node,field,value,depth):
		if field == "body":
			Type_tree_dict_interface.change_try_states('in_body')
			if isinstance(value, list):
				for element in value:
					self.mark_ast_tree(element,depth+1,True)
			elif isinstance(value, ast.AST):
				self.mark_ast_tree(value,depth+1,True)
		elif field =="handlers":
			Type_tree_dict_interface.change_try_states('in_handlers')
			if isinstance(value, list):
				for element in value:
					Type_tree_dict_interface.handler_copies_try_create_copies_all(self.variable_types_dictionary)
					self.mark_ast_tree(element,depth+1,True)
					Type_tree_dict_interface.handler_copies_try_finished_handler_all(self.variable_types_dictionary)
			elif isinstance(value, ast.AST):
				Type_tree_dict_interface.handler_copies_try_create_copies_all(self.variable_types_dictionary)
				self.mark_ast_tree(value,depth+1,True)
				Type_tree_dict_interface.handler_copies_try_finished_handler_all(self.variable_types_dictionary)
			else:
				raise Exception('value should be either a list or ast.AST')
			Type_tree_dict_interface.handler_copies_try_delete_original_premature_all(self.variable_types_dictionary)
		elif field == "orelse":
			Type_tree_dict_interface.change_try_states('in_orelse')
			Type_tree_dict_interface.enter_try_field_all(self.variable_types_dictionary,field)
			if isinstance(value, list):
				for element in value:
					self.mark_ast_tree(element,depth+1,True)
			elif isinstance(value, ast.AST):
				self.mark_ast_tree(value,depth+1,True)
			else:
				raise Exception('value should be either a list or ast.AST')
		elif field == "finalbody":
			Type_tree_dict_interface.change_try_states('in_finalbody')
			Type_tree_dict_interface.enter_try_field_all(self.variable_types_dictionary,field)
			if isinstance(value, list):
				for element in value:
					self.mark_ast_tree(element,depth+1,True)
			elif isinstance(value, ast.AST):
				self.mark_ast_tree(value,depth+1,True)
			else:
				raise Exception('value should be either a list or ast.AST')
				
	def determine_AnnAssign(self,node):
		if type(node.target) == ast.Name:
			type_node = None
			if hasattr(node.value,self.mark_name):
				type_node = node.value
			elif hasattr(node.annotation,self.mark_name):
				type_node = node.annotation
			else:
				return {UnknownType}
			self.set_variable_type(node.target,getattr(type_node,self.mark_name))
			setattr(node.target,self.mark_name,getattr(type_node,self.mark_name))
		return {UnknownType}
	def determine_Assign(self,node):
		if type(node.targets[0]) == ast.Tuple:
			if type(node.value) == ast.Tuple or type(node.value) == ast.List:
				for variable,value in zip(node.targets[0].elts, node.value.elts):
					if hasattr(value,self.mark_name):
						setattr(variable,self.mark_name,getattr(value,self.mark_name))
						self.set_variable_type(variable,getattr(value,self.mark_name))		
		elif type(node.targets[0]) == ast.Name:
			if hasattr(node.value,self.mark_name):					
				self.set_variable_type(node.targets[0],getattr(node.value,self.mark_name))
				setattr(node.targets[0],self.mark_name,getattr(node.value,self.mark_name))
		return {UnknownType}
	def determine_arg(self,node):
		return self.type_from_dictionary(node.arg)
	def determine_BinOp(self,node):
		if not (hasattr(node.left,self.mark_name) and hasattr(node.right,self.mark_name)):
			return {UnknownType}
		left_types = getattr(node.left,self.mark_name)
		right_types = getattr(node.right,self.mark_name)
		if left_types is None or right_types is None:
			return {UnknownType}
		if isinstance(left_types,type):
			left_types = {left_types}
		if isinstance(right_types,type):
			right_types = {right_types}
			
		possible_types = check_for_types_with_node(left_types,right_types,node.op)
		
		if len(possible_types) == 0:
			return {UnknownType}
		return possible_types
	def determine_BoolOp(self,node):
		return {bool}
	def determine_Call(self,node):
		return self.type_from_return_dictionary(node.func)
	def determine_Compare(self,node):
		return {bool}
	def determine_Dict(self,node):
		return {dict}
	def determine_List(self,node):
		return {list}
	def determine_Module(self,node):
		return {UnknownType}
	def determine_Name(self,node):
		if not node.id in self.variable_types_dictionary:
			toReturn = locate(node.id)
			if toReturn is not None:
				return toReturn
		toReturn = self.type_from_dictionary(node.id)
		return toReturn
	def determine_NameConstant(self,node):
		return {bool}
	def determine_Num(self,node):
		if type(node.n) == int:
			return {int}
		elif type(node.n) == float:
			return {float}
		elif type(node.n) == complex:
			return {complex}
	def determine_Str(self,node):
		return {str}
	def determine_Subscript(self,node):
		#not fully implemented
		container_type_name = node.value.id
		if container_type_name == "Any":
			return {UnknownType} 
		elif container_type_name == 'AnyStr':
			return {str,bytes}
		elif container_type_name == 'ClassVar':
			return {UnknownType}
		elif container_type_name == "Dict":
			return {dict}
		elif container_type_name == "List":
			return {list}
		elif container_type_name == 'Optional':
			if (hasattr(node.slice,self.mark_name)):
				return getattr(node.slice,self.mark_name)
			union_types = {UnknownType}
			slice_type = type(node.slice)	
			if slice_type == ast.Name:
				return union_types | determine_Name(node.slice)
			elif slice_type == ast.Index:
				value_type = type(node.slice.value)
				if value_type == ast.Name:
					return union_types | determine_Name(node.slice)
				elif value_type == ast.Tuple:
					for elt in node.slice.value.elts:
						toAdd = determine_type(elt)
						if type(toAdd) == set:
							union_types |= toAdd
						else:
							union_types.add(toAdd)
					return union_types
			else:
				return {UnknownType}
		elif container_type_name == "Set":
			return {set}
		elif container_type_name == "Text":
			return {str}
		elif container_type_name == "Tuple":
			return {tuple}
		elif container_type_name == 'Union':
			if (hasattr(node.slice,self.mark_name)):
				return getattr(node.slice,self.mark_name)
			union_types = set()
			slice_type = type(node.slice)	
			if slice_type == ast.Name:
				return determine_Name(node.slice)
			elif slice_type == ast.Index:
				value_type = type(node.slice.value)
				if value_type == ast.Name:
					return determine_Name(node.slice)
				elif value_type == ast.Tuple:
					for elt in node.slice.value.elts:
						toAdd = determine_type(elt)
						if type(toAdd) == set:
							union_types |= toAdd
						else:
							union_types.add(toAdd)
					return union_types
			else:
				return {UnknownType}
		
		return {UnknownType}	
			
	def determine_type(self,node):
		if not isinstance(node, ast.AST):
			return NotAnASTNodeType
		name = "determine_"+node.__class__.__name__
		if not hasattr(annotationMarker,name):
			controlledPrint("* determine_type: Unknown Type for "+node.__str__())
			return {UnknownType}
		else:
			fun = getattr(annotationMarker,name)
			toReturn = fun(self,node)
			
			typeName = " not known "
			if hasattr(toReturn,'__name__'):
				typeName = toReturn.__name__
			elif hasattr(toReturn,'__str__'):
				typeName = toReturn.__str__()
			controlledPrint("* determine_type: "+typeName+" for "+node.__str__()+" function "+fun.__name__)
			
			return toReturn
				
	def annotation_to_type(self,node):
		if type(node) == ast.Name:
			return locate(node.id)
		elif type(node) == ast.Subscript:
			return determine_Subscript(node)
		return None
	
	def fill_return_values_of_build_in_functions(self):
		pass
	
	def set_variable_type(self,node,typeToReplace):
		if type(typeToReplace) == type or type(typeToReplace) == set:
			name = ""
			if type(node) == ast.Name:
				name = node.id
			elif type(node) == ast.arg:
				name = node.arg
			elif type(node) == str:
				name = node
			else:
				return
			Type_tree_dict_interface.set_variable_type(self.variable_types_dictionary,name,typeToReplace)
			#if name not in self.variable_types_dictionary:
			#	self.variable_types_dictionary[name] = Type_tree_interface(name)
			#self.variable_types_dictionary[name].add_type(typeToReplace)
		
	def determine_return_types(self,node):
		for n in node.body:
			if type(n) == ast.FunctionDef:
				type_to_set = self.annotation_to_type(n.returns)
				if type_to_set is None:
					self.return_types_dictionary[n.name] = UnknownType
				else:
					self.return_types_dictionary[n.name] = type_to_set
	
	def increase_nest_level(self):
		self.dictionary_level+=1
		self.list_of_nested_variable_types_dictionaries.append(copy.copy(self.variable_types_dictionary))
		self.variable_types_dictionary = {}
	
	def decrease_nest_level(self):
		if self.dictionary_level>0:
			self.dictionary_level-=1
			self.variable_types_dictionary = self.list_of_nested_variable_types_dictionaries.pop()
			
	def increase_nest_return_level(self):
		self.return_dictionary_level+=1
		self.list_of_nested_return_types_dictionaries.append(copy.copy(self.return_types_dictionary))
		self.return_types_dictionary = {}
		
	def decrease_nest_return_level(self):
		if self.return_dictionary_level>0:
			self.return_dictionary_level-=1
			self.return_types_dictionary = self.list_of_nested_return_types_dictionaries.pop()
	
	def type_from_dictionary(self,name):
		if name in self.variable_types_dictionary:
			return self.variable_types_dictionary[name].get_type_set()
		for dictionary in reversed(self.list_of_nested_variable_types_dictionaries):
			if name in dictionary:
				return dictionary[name].get_type_set()
		return {UnknownType}
	
	def type_from_return_dictionary(self,node):
		name = ""
		if type(node) == ast.Name:
			name = node.id
		else:
			return {UnknownType}
		if name in self.return_types_dictionary:
			return self.return_types_dictionary[name]
		for dictionary in reversed(self.list_of_nested_return_types_dictionaries):
			if name in dictionary:
				return dictionary[name]
		return {UnknownType}	
		
class annotationMarker36(annotationMarker):
	__python_version__ = (3,6)
	
	def fill_return_values_of_build_in_functions(self):
		#self.return_types_dictionary[function_name] = returned_type
		# only suitable types are ones with argumentless constructor
		self.return_types_dictionary['abs'] = {int,float}
		self.return_types_dictionary['all'] = {bool}
		self.return_types_dictionary['any'] = {bool}
		self.return_types_dictionary['ascii'] = {str}
		self.return_types_dictionary['bin'] = {str}
		self.return_types_dictionary['bool'] = {bool}
		self.return_types_dictionary['bytearray'] = {bytearray}
		self.return_types_dictionary['bytes'] = {bytes}
		self.return_types_dictionary['chr'] = {str}
		self.return_types_dictionary['complex'] = {complex}
		self.return_types_dictionary['dict'] = {dict}
		self.return_types_dictionary['divmod'] = {tuple}
		self.return_types_dictionary['float'] = {float}
		self.return_types_dictionary['format'] = {str}
		self.return_types_dictionary['frozenset'] = {frozenset}
		self.return_types_dictionary['getattr'] = {UnknownType}
		self.return_types_dictionary['globals'] = {dict}
		self.return_types_dictionary['hasattr'] = {bool}
		self.return_types_dictionary['hash'] = {int}
		self.return_types_dictionary['hex'] = {str}
		self.return_types_dictionary['id'] = {int}
		self.return_types_dictionary['input'] = {str}
		self.return_types_dictionary['int'] = {int}
		self.return_types_dictionary['isinstance'] = {bool}
		self.return_types_dictionary['issubclass'] = {bool}
		self.return_types_dictionary['len'] = {int}
		self.return_types_dictionary['list'] = {list}
		self.return_types_dictionary['locals'] = {dict}
		self.return_types_dictionary['object'] = {object}
		self.return_types_dictionary['oct'] = {str}
		self.return_types_dictionary['ord'] = {int}
		self.return_types_dictionary['pow'] = {int,float,complex}
		self.return_types_dictionary['repr'] = {str}
		self.return_types_dictionary['round'] = {int,float}
		self.return_types_dictionary['set'] = {set}
		self.return_types_dictionary['int'] = {int}
		self.return_types_dictionary['sorted'] = {list}
		self.return_types_dictionary['str'] = {str}
		self.return_types_dictionary['sum'] = {int,float,complex}
		self.return_types_dictionary['tuple'] = {tuple}
		self.return_types_dictionary['type'] = {type}
		
		#------ retuns augumented type
		
		augumentedType = Type_tree.augumentedTypeInfo(range)
		self.return_types_dictionary['range'] = augumentedType
		
class Type_tree():
	fake_last_added = 'fake_last_added'
	class outer_node():
		def __init__(self,parent):
			self.parent = parent
			self.children = set()
			self.breakable = False
			self.breakable_try = False
		def add_child(self,child):
			self.children.add(child)
		def remove_child(self,child):
			self.children.remove(child)
		def __str__(self):
			return "outer_node children:{0},  breakable:{1}, breakable_try:{2}".format(len(self.children),str(self.breakable),str(self.breakable_try))
	class inner_node(outer_node):
		try_state_dict={'not_in_try':1,'original_premature':2,'copied_premature':3,'finished_premature':4,'full_for_else':5,'copied_premature_last_added':6}
		def __init__(self,parent,new_type):
			super().__init__(parent)
			self.type = new_type
			self.try_status = Type_tree.inner_node.try_state_dict['not_in_try']
		def set_try_status(self,status):
			if not status in Type_tree.inner_node.try_state_dict:
				raise Exception('try status \''+status.__str__()+'\' does not exist')
			self.try_status = Type_tree.inner_node.try_state_dict[status]
		def is_try_status(self,status):
			if not status in Type_tree.inner_node.try_state_dict:
				raise Exception('try status \''+status.__str__()+'\' does not exist')
			if self.try_status == Type_tree.inner_node.try_state_dict[status]:
				return True
			return False
		def __str__(self):
			return "inner_node type:{0} children:{1} try:{2} fake_last_added:{3}".format(self.type,len(self.children),self.try_status,hasattr(self,'fake_last_added'))
	class augumentedTypeInfo:
		def __init__(self,type,ctype=UnknownType):
			self.type = type
			if type is range:
				self.contentType = int
				self.knownContent = type(0)
			else:
				self.contentType = ctype
				self.knownContent = type()
		def addItemToContent(self,item,key=None):
			if isinstance(self.knownContent,set):
				self.knownContent.add(item)
			elif isinstance(self.knownContent,list):
				self.knownContent.append(item)
			elif isinstance(self.knownContent,dict):
				self.knownContent[key] = item
			elif isinstance(self.knownContent,tuple):
				self.knownContent = self.knownContent + (item,)
			elif isinstance(self.knownContent,range):
				raise Exception('Attempt on adding an item to range type. It is impossible.')
			else:
				raise Exception('augumentedTypeInfo type of the knownContent iterable is not supported')
		def __call__(self,var=None):
			if var is None:
				return self.type()
			else:
				return self.type(var)
		def getKnownContent(self):
			return self.knownContent

	def __init__(self,variable_name):
		self.name = variable_name
		self.root = Type_tree.inner_node(None,IgnorableType)
		self.last_added = self.root
		
	
	def add_replace(self,new_type):
		self.last_added.type = new_type
		self.last_added.children.clear()		
		controlledPrint("{0} add_replace {1}".format(self.name,new_type)+" "+self.__str__())
	
	def add_if(self,new_type):
		new_node_o = Type_tree.outer_node(self.last_added)
		self.last_added.add_child(new_node_o)
		new_node_i = Type_tree.inner_node(new_node_o,new_type)
		new_node_o.add_child(new_node_i)
		self.last_added = new_node_i
		controlledPrint("{0} add_if {1}".format(self.name,new_type)+" "+self.__str__())
	
	def add_elif(self,new_type):
		new_node_i = Type_tree.inner_node(self.last_added.parent,new_type)
		self.last_added.parent.add_child(new_node_i)
		self.last_added = new_node_i		
		controlledPrint("{0} add_elif {1}".format(self.name,new_type)+" "+self.__str__())
	
	def end_if(self,new_type=None):
		self.last_added = self.last_added.parent.parent
		controlledPrint("{0} end_if".format(self.name)+" "+self.__str__())
	
	def pass_break(self,new_type=None):
		node_to_copy = self.last_added
		while node_to_copy.parent is not None:
			if node_to_copy.parent.breakable:
				break
			node_to_copy = node_to_copy.parent.parent
		else:
			raise Exception('Couldn\'t find breakable loop node in Type Tree when break was ecountered.')
		copy_node = self.subtree_copy_inner(node_to_copy)
		node_to_copy.parent.add_child(copy_node)
		controlledPrint("{0} pass_break".format(self.name)+" "+self.__str__())
	
	#Creates a copy of a type_tree node later for handlers.
	def try_after_assign(self):
		node_to_copy = self.last_added
		while node_to_copy.parent is not None:
			if node_to_copy.parent.breakable_try:
			#if node_to_copy.parent.breakable:
				break
			node_to_copy = node_to_copy.parent.parent
		else:
			raise Exception('Couldn\'t find breakable_try loop node in Type Tree when break was ecountered.')
		copy_node = self.subtree_copy_inner_with_try_status(node_to_copy,'original_premature')
	
		node_to_copy.parent.add_child(copy_node)
		controlledPrint("{0} try_after_assign".format(self.name)+" "+self.__str__())
		
		return copy_node
	def get_type_set(self):
		if len(self.last_added.children) == 0:
			toReturn = None
			if self.last_added.type == IgnorableType:
				toReturn = self.get_parent_type(self.last_added)
			else:
				toReturn = self.last_added.type
			if isinstance(toReturn,type):
				return {toReturn}
			else:
				return toReturn
		set_to_return = set()
		for outer_node in self.last_added.children:
			for inner_node in outer_node.children:
				memory_last_added = self.last_added
				self.last_added = inner_node
				states = self.get_type_set()
				self.last_added = memory_last_added
				if IgnorableType in states:
					states.remove(IgnorableType)
					if self.last_added.type is type: #If it is not type, then it is a set of types
						states.add(self.last_added.type)
					else:
						states |= self.last_added.type
				set_to_return|=states
		return set_to_return
	def get_parent_type(self,node):
		if node.parent is not None:
			if node.parent.parent is not None:
				if hasattr(node.parent.parent,'type'):
					if node.parent.parent.type == IgnorableType:
						return self.get_parent_type(node.parent.parent)
					else:
						return node.parent.parent.type
		return {UnknownType}
	
	def find_breakable_children(self,state):
		def find_breakable(node):
			if hasattr(node,'breakable') and getattr(node,'breakable'):
				return node
			return find_breakable(node.parent)
		breakable_parent = find_breakable(self.last_added)
		list = []
		for child in breakable_parent.children:
			if  state == "all" or child.is_try_status(state):
				list.append(child)
		return list
	def find_breakable_try_children(self,state):
		def find_breakable_try(node):
			if hasattr(node,'breakable_try') and getattr(node,'breakable_try'):
				return node
			return find_breakable_try(node.parent)
		breakable_parent = find_breakable_try(self.last_added)
		list = []
		for child in breakable_parent.children:
			if  state == "all" or child.is_try_status(state):
				list.append(child)
		return list

	def find_fake_last_added(self,node):
		def recursion_find(node):
			if hasattr(node,Type_tree.fake_last_added) and getattr(node,Type_tree.fake_last_added):
				return node
			for child in node.children:
				return recursion_find(child)
		return recursion_find(node)
	def set_if_breakable(self,is_loop):
		self.last_added.parent.breakable = is_loop
	def set_if_breakable_try(self,is_try):
		self.last_added.parent.breakable_try = is_try
	def set_last_added_try_status(self,status):
		self.last_added.set_try_status(status)
	def subtree_copy_inner(self,node):
		root = Type_tree.inner_node(node.parent,node.type)
		if node == self.last_added:
			setattr(root,Type_tree.fake_last_added,True)
		if hasattr(node,Type_tree.fake_last_added) and getattr(node,Type_tree.fake_last_added):
			setattr(root,Type_tree.fake_last_added,True)
		for outer_child in node.children:
			new_outer = Type_tree.outer_node(root)
			for inner_child in outer_child.children:
				new_outer.add_child(self.subtree_copy_inner(inner_child))
			root.add_child(new_outer)
		return root
	def subtree_copy_inner_with_try_status(self,node,status):
		def recursion_status_change(node,status):
			if hasattr(node,'try_status'):
				node.set_try_status(status)
			for child in node.children:
				recursion_status_change(child,status)		
		root = self.subtree_copy_inner(node)
		recursion_status_change(root,status)
		return root
	def __str__(self):
		return "name "+self.name.__str__()+"\n"+self.node_string(self.root)	
	def node_string(self,node,level=0):
		space = level*"  "
		if self.last_added == node:
			space+='*'
		toReturn = space+node.__str__()+'\n'
		for child in node.children:
			toReturn+=self.node_string(child,level+1)
		return toReturn
	
class Type_tree_interface():
	def __init__(self,variable_name):
		self.tree= Type_tree(variable_name)
		self.state_dictionary = {'normal':1,'if':2,'elif':3,'try_body':4}
		self.state = self.state_dictionary['normal']
		self.state_queue = []	

		self.try_state_dictionary={'not_try':1,'in_body':2,'in_handlers':3,'in_orelse':4,'in_finalbody':5}
		self.try_state = self.try_state_dictionary['not_try']
		self.try_state_queue = []
		
		self.handlers_state_queue_dictionary = {}
		self.handlers_state = self.state_dictionary['normal']
		self.handlers_state_queue_dictionary_id = 1
		
	def make_copy(self):
		return copy.deepcopy(self)
		
	def change_state(self,state_name):
		if state_name == 'normal':
			self.state = self.state_dictionary[state_name]
		elif state_name == 'if':
			self.state = self.state_dictionary[state_name]
			self.tree.add_if(IgnorableType)
		elif state_name == 'elif':
			self.state = self.state_dictionary[state_name]
			self.tree.add_elif(IgnorableType)
		elif state_name == 'try_body':
			self.state = self.state_dictionary[state_name]
			self.tree.add_if(IgnorableType)
			self.tree.set_last_added_try_status('full_for_else')
			self.tree.set_if_breakable_try(True)
		elif state_name == 'try_handlers':
			self.state = self.state_dictionary[state_name]
		elif state_name == 'try_else':
			self.state = self.state_dictionary[state_name]
	
	def change_try_state(self,state_name):
		controlledPrint('change_try_state: '+state_name+" name: "+self.tree.name)
		self.try_state = self.try_state_dictionary[state_name]
		controlledPrint("{0} change_try_state ".format(self.tree.name)+" "+self.tree.__str__())
	
	def enter_ast_If(self):
		controlledPrint('enter ast if')
		self.state_queue.append(self.state)
		self.change_state('if')
	
	def enter_loop(self):
		controlledPrint('enter loop')
		self.state_queue.append(self.state)
		self.change_state('if')
		self.tree.set_if_breakable(True)
	
	def enter_try(self):
		#'not_try':1,'in_body':2,'in_handlers':3,'in_orelse':4,'in_finalbody':5
		self.state_queue.append(self.state)
		self.change_state('try_body')
		self.enter_try_field('body')
		controlledPrint("{0} enter_try ".format(self.tree.name)+" "+self.tree.__str__())
		
	def enter_try_field(self,field):
		if field == 'body':
			self.change_try_state('in_body')
		elif field == 'handlers':
			self.change_try_state('in_handlers')
		elif field == 'orelse':
			self.change_try_state('in_orelse')
		elif field == 'finalbody':
			self.change_try_state('in_finalbody')	
		elif field == 'not_try':
			self.change_try_state('not_try')
			
	def exit_try(self):
		controlledPrint('called exit_try')
		self.enter_try_field('not_try')
		self.state = self.state_queue.pop()
		self.handlers_state_queue_dictionary = {}
			
	def handler_copies_try_create_copies(self):	
		parent = self.tree.last_added.parent
		list_for_copy = []
		controlledPrint("{0} handler_copies_try_create_copies (before) ".format(self.tree.name)+" "+self.tree.__str__())
		for child in parent.children:
			if child.is_try_status('original_premature'): 
				list_for_copy.append(child)
		for to_copy in list_for_copy:
			copied = self.tree.subtree_copy_inner_with_try_status(to_copy,'copied_premature')
			parent.add_child(copied)
		self.enter_try_field('handlers')		
		controlledPrint("{0} handler_copies_try_create_copies (after) ".format(self.tree.name)+" "+self.tree.__str__())
		
		if not 'original' in self.handlers_state_queue_dictionary:
			self.handler_copies_add_Type_tree_state_queue(self.state_queue,'original')
		self.state_queue = []
		self.state = self.state_dictionary['normal']
		
	def handler_copies_try_finished_handler(self):	
		parent = self.tree.last_added.parent
		list_to_change = []
		for child in parent.children:
			if child.is_try_status('copied_premature'): 
				list_to_change.append(child)
		for to_change in list_to_change:
			to_change.set_try_status('finished_premature')
		
	def handler_copies_try_delete_original_premature(self):
		parent = self.tree.last_added.parent
		list_for_delete = []
		for child in parent.children:
			if child.is_try_status('original_premature'): 
				list_for_delete.append(child)
		for to_delete in list_for_delete:
			parent.children.remove(to_delete)
		self.state_queue = self.handler_copies_get_Type_tree_state_queue('original')
		
	def handler_copies_add_Type_tree_state_queue(self,queue,id):
		self.handlers_state_queue_dictionary[id] = copy.copy(queue)
	
	def handler_copies_get_Type_tree_state_queue(self,id):
		return self.handlers_state_queue_dictionary[id]
	
	def enter_orelse(self):
		if self.try_state == self.try_state_dictionary['not_try'] or self.try_state == self.try_state_dictionary['in_body']:
			if self.state == self.state_dictionary['if'] or self.state == self.state_dictionary['elif'] or self.state == self.state_dictionary['try_body']:
				self.change_state('elif')
			else:
				raise Exception('enter_orelse with invalid state of variable:'+self.tree.name)
		elif self.try_state == self.try_state_dictionary['in_handlers']:
			self.state = self.state_dictionary['elif']
			self.handler_version(None,'add_elif','copied_premature')
		elif self.try_state == self.try_state_dictionary['in_orelse']:
			self.state = self.state_dictionary['elif']
			self.handler_version(None,'add_elif','full_for_else')
		elif self.try_state == self.try_state_dictionary['in_finalbody']:
			self.state = self.state_dictionary['elif']
			self.handler_version(None,'add_elif','all')
	
	def exit_ast_If(self):
		controlledPrint("{0} exit_ast_If".format(self.tree.name))
		if self.try_state == self.try_state_dictionary['not_try'] or self.try_state == self.try_state_dictionary['in_body']:
			if self.state == self.state_dictionary['if'] or self.state == self.state_dictionary['elif'] or self.state == self.state_dictionary['try_body']:
				self.state = self.state_queue.pop()
				self.tree.end_if()
			else:
			#exit_ast_If with invalid state, which means a variable was created inside a loop. Nothing happens
			#raise Exception('exit_ast_If with invalid state')
				pass
		elif self.try_state == self.try_state_dictionary['in_handlers']:
			self.state = self.state_queue.pop()
			self.handler_version(None,'end_if','copied_premature')
		elif self.try_state == self.try_state_dictionary['in_orelse']:
			self.state = self.state_queue.pop()
			self.handler_version(None,'end_if','full_for_else')
		elif self.try_state == self.try_state_dictionary['in_finalbody']:
			self.state = self.state_queue.pop()
			self.handler_version(None,'end_if','all')
	def loop_break(self):	
		if self.try_state == self.try_state_dictionary['not_try'] or self.try_state == self.try_state_dictionary['in_body']:
			if self.state == self.state_dictionary['if'] or self.state == self.state_dictionary['elif'] or self.state == self.state_dictionary['try_body']:
				self.tree.pass_break()
			else:
				raise Exception('loop_break while not in loop')
		elif self.try_state == self.try_state_dictionary['in_handlers']:
			if self.state == self.state_dictionary['if'] or self.state == self.state_dictionary['elif'] or self.state == self.state_dictionary['try_body']:
				self.handler_version(None,'pass_break','copied_premature')	
			else:
				raise Exception('loop_break while not in loop')
		elif self.try_state == self.try_state_dictionary['in_orelse']:
			if self.state == self.state_dictionary['if'] or self.state == self.state_dictionary['elif'] or self.state == self.state_dictionary['try_body']:
				self.handler_version(None,'pass_break','full_for_else')
			else:
				raise Exception('loop_break while not in loop')
		elif self.try_state == self.try_state_dictionary['in_finalbody']:
			if self.state == self.state_dictionary['if'] or self.state == self.state_dictionary['elif'] or self.state == self.state_dictionary['try_body']:
				self.handler_version(None,'pass_break','all')
			else:
				raise Exception('loop_break while not in loop')
				
	def add_type(self,type):
		controlledPrint("add_type try_state:"+self.dictionary_state_to_name(self.try_state_dictionary,self.try_state))
		if self.try_state == self.try_state_dictionary['not_try']:
			if self.state == self.state_dictionary['if'] or self.state == self.state_dictionary['elif'] or self.state == self.state_dictionary['normal']:
				self.tree.add_replace(type)
		elif self.try_state == self.try_state_dictionary['in_body']:
			if self.state == self.state_dictionary['try_body']:
				self.tree.add_replace(type)
				copy = self.tree.try_after_assign()
				copy.set_try_status('original_premature')
		elif self.try_state == self.try_state_dictionary['in_handlers']:
			self.handler_version(type,'add_replace','copied_premature')
		elif self.try_state == self.try_state_dictionary['in_orelse']:
			self.handler_version(type,'add_replace','full_for_else')
		elif self.try_state == self.try_state_dictionary['in_finalbody']:
			self.handler_version(type,'add_replace','all')
		
	def get_type_set(self):
		return self.tree.get_type_set()
	
	def handler_version(self,new_type,function_name,children_try_state):
		list = self.tree.find_breakable_try_children(children_try_state)
		last_added_storage = self.tree.last_added
		for node in list:
			fake_la = self.tree.find_fake_last_added(node)
			if fake_la is None:
				fake_la = last_added_storage
				change_attribute = False
			else:
				change_attribute = True
			self.tree.last_added = fake_la
			func = getattr(self.tree,function_name)
			
			func(new_type)
			
			if change_attribute:
				delattr(fake_la,Type_tree.fake_last_added)
				setattr(self.tree.last_added,Type_tree.fake_last_added,True)
		self.tree.last_added = last_added_storage
	
	def __str__(self):
		return "state: {0} {1}".format(self.state,self.tree.get_type_set().__str__())
	
	def dictionary_state_to_name(self,dictionary,state):
		for key,value in dictionary.items():
			if value == state:
				return key

class Type_tree_dict_interface():
	try_state_dictionary={'not_try':1,'in_body':2,'in_handlers':3,'in_orelse':4,'in_finalbody':5}
	try_state = try_state_dictionary['not_try']
	try_state_queue = []
	type_tree_to_replicate = Type_tree_interface('placeholder name')
	
	def class_initialisation():
		Type_tree_dict_interface.type_tree_to_replicate.add_type(UnknownType)
	
	def handler_copies_try_create_copies_all(dict):
		for tree in dict:
			dict[tree].handler_copies_try_create_copies()
		Type_tree_dict_interface.type_tree_to_replicate.handler_copies_try_create_copies()
	
	def handler_copies_try_finished_handler_all(dict):
		for tree in dict:
			dict[tree].handler_copies_try_finished_handler()
		Type_tree_dict_interface.type_tree_to_replicate.handler_copies_try_finished_handler()
	def handler_copies_try_delete_original_premature_all(dict):
		for tree in dict:
			dict[tree].handler_copies_try_delete_original_premature()	
		Type_tree_dict_interface.type_tree_to_replicate.handler_copies_try_delete_original_premature()
	def enter_loop_all(dict):
		for tree in dict:
			dict[tree].enter_loop()
		Type_tree_dict_interface.type_tree_to_replicate.enter_loop()
	
	def loop_break_all(dict):
		for tree in dict:
			dict[tree].loop_break()
		Type_tree_dict_interface.type_tree_to_replicate.loop_break()
	
	def exit_ast_If_all(dict):
		for tree in dict:
			dict[tree].exit_ast_If()
		Type_tree_dict_interface.type_tree_to_replicate.exit_ast_If()
	
	def enter_ast_If_all(dict):
		for tree in dict:
			dict[tree].enter_ast_If()
		Type_tree_dict_interface.type_tree_to_replicate.enter_ast_If()
	
	def enter_orelse_all(dict):
		for tree in dict:
			dict[tree].enter_orelse()
		Type_tree_dict_interface.type_tree_to_replicate.enter_orelse()	

	def enter_try_all(dict):
		for tree in dict:
			dict[tree].enter_try()
		Type_tree_dict_interface.type_tree_to_replicate.enter_try()
	
	def enter_try_field_all(dict,field):
		Type_tree_dict_interface.change_try_states('in_'+field)
		for tree in dict:
			dict[tree].enter_try_field(field)
	
	def exit_try_all(dict):
		Type_tree_dict_interface.change_try_states('not_try')
		for tree in dict:
			dict[tree].exit_try()
		Type_tree_dict_interface.type_tree_to_replicate.exit_try()

	def change_try_states(state):
		Type_tree_dict_interface.try_state = Type_tree_dict_interface.try_state_dictionary[state]
		
	def set_variable_type(dict,name,typeToReplace):
		controlledPrint('set_variable_type name:'+name)
		dont_add_type = False
		if name not in dict:
			controlledPrint('not in dict')
			#if Type_tree_dict_interface.try_state == Type_tree_dict_interface.try_state_dictionary['not_try']:
			#	dict[name] = Type_tree_interface(name)
			#else:
			#	dict[name] = copy.deepcopy(Type_tree_dict_interface.type_tree_to_replicate)
			dict[name] = copy.deepcopy(Type_tree_dict_interface.type_tree_to_replicate)
			dict[name].tree.add_replace(typeToReplace)
		else:
			controlledPrint('in dict')
			dict[name].add_type(typeToReplace)
	
				
def get_annotation_manager(is_enabled):
	if is_enabled:
		return annotationManager()
	else:
		return annotationManagerDisabled()
	
def get_annotation_marker(is_enabled):
	if is_enabled:
		return utils.get_by_python_version([annotationMarker36])()
	else:
		return annotationMarkerDisabled()