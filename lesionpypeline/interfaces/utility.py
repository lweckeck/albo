import numpy as np
import nipype.interfaces.base as base
import nipype.interfaces.io as nio
import nipype.interfaces.utility as util

class InsertInputSpec(base.BaseInterfaceInputSpec):
    """Input specification for Insert class"""
    value = base.traits.Any(desc='Value to insert into list')
    index = base.traits.Int(desc='Index to insert value before')
    inlist = base.traits.List(desc='List to insert value into')

class InsertOutputSpec(base.TraitedSpec):
    """Output specification for Insert class"""
    out = base.traits.List(desc='List with inserted value')

class Insert(nio.IOBase):
    """Basic interface class to insert a value into a list before a given index, based on python's List.insert semantics
    Examples
    --------
    >>> from lesionpypeline.interfaces.utility import Insert
    >>> ins = Insert()
    >>> ins.inputs.value = 10
    >>> ins.inputs.index = 2
    >>> ins.inputs.inlist = [0,1,2,3,4,5]
    >>> out = ins.run()
    >>> out.outputs.out
    [0, 1, 10, 2, 3, 4, 5]
    """
    input_spec = InsertInputSpec
    output_spec = InsertOutputSpec

    def _list_outputs(self):
        outputs = self.output_spec().get()
        l = self.inputs.inlist
        l.insert(self.inputs.index, self.inputs.value)
        outputs['out'] = l

        return outputs
            

class TeeInputSpec(base.BaseInterfaceInputSpec):
    """Input specification for Tee class"""
    inlist = base.InputMultiPath(base.traits.Any, mandatory=True,
                  desc='list of values to choose from')
    index = base.InputMultiPath(base.traits.Int, mandatory=True,
                           desc='0-based indices of values to send to selected, the rest goes to rejected')

class TeeOutputSpec(base.TraitedSpec):
    """Output specification for Tee class"""
    selected = base.OutputMultiPath(base.traits.Any, desc='list of values designated for selected')
    rejected = base.OutputMultiPath(base.traits.Any, desc='list of remaining values')

class Tee(nio.IOBase):
    """Basic interface class to select values from a list based on indices, and output the selected values as well as the not selected values
    Examples
    --------
    >>> from lesionpypeline.interfaces.utility import Tee
    >>> t = Tee()
    >>> t.inputs.inlist = [10,20,30,40,50]
    >>> t.inputs.index = [2,3]
    >>> out = t.run()
    >>> out.outputs.selected
    [30, 40]
    >>> out.outputs.rejected
    [10, 20, 50]
    """
    input_spec = TeeInputSpec
    output_spec = TeeOutputSpec

    def _list_outputs(self):
        outputs = self._outputs().get()
        selected_indices = self.inputs.index
        filtered_indices = [i for i in range(len(self.inputs.inlist)) if i not in selected_indices]
        
        outputs['selected'] = [self.inputs.inlist[i] for i in selected_indices]
        outputs['rejected'] = [self.inputs.inlist[i] for i in filtered_indices]
        return outputs
        
    
