from typing import Dict, Iterator, Optional


class TreeNode:
    _id: int
    _input_value: bool
    _output_value: Optional[bool]
    _children: Dict[int, 'TreeNode']

    class TreeIterator:
        _tree: 'TreeNode'
        _iterator: Iterator

        def __init__(self, tree: 'TreeNode'):
            self._tree = tree
            self._iterator = iter(tree._children)

        def __next__(self) -> 'TreeNode':
            return self._tree[self._iterator.__next__()]

    def __init__(self, id_: int, input_value: bool, children: Optional[Dict[int, 'TreeNode']] = None,
                 output_value: Optional[bool] = None):
        self._id = id_
        self._input_value = input_value
        self._children = children if children is not None else {}
        self._output_value = output_value

    @property
    def id(self) -> int:
        return self._id

    @property
    def input_value(self) -> bool:
        return self._input_value

    @property
    def children_count(self) -> int:
        return len(self._children)

    @property
    def output_value(self) -> Optional[bool]:
        return self._output_value

    @output_value.setter
    def output_value(self, output_value: Optional[bool]):
        self._output_value = output_value

    def __getitem__(self, children_id: int) -> 'TreeNode':
        if not isinstance(children_id, int):
            raise TypeError(f'key must be integer, not {children_id.__class__}')
        return self._children[children_id]

    def __setitem__(self, children_id: int, tree: 'TreeNode'):
        if not isinstance(children_id, int):
            raise TypeError(f'key must be integer, not {children_id.__class__}')
        if not isinstance(tree, TreeNode):
            raise TypeError(f'value must be TreeNode, not {tree.__class__}')
        self._children[children_id] = tree

    def get(self, children_id: int, default: Optional['TreeNode'] = None) -> Optional['TreeNode']:
        if not isinstance(children_id, int):
            raise TypeError(f'key must be integer, not {children_id.__class__}')
        if default is not None and not isinstance(default, TreeNode):
            raise TypeError(f'default must be TreeNode, not {default.__class__}')
        if children_id in self._children:
            return self._children[children_id]
        else:
            return default

    def __iter__(self):
        return self.TreeIterator(self)

    def __str__(self, level: int = 0):
        padding = '\t' * level
        ret = f'{padding}{self._id}, {self._input_value}, {self._output_value}\n'
        for child in self._children.values():
            ret += child.__str__(level + 1)
        return ret
