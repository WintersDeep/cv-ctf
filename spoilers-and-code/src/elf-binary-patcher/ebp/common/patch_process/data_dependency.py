# python imports
from typing import Iterator, TypeVar, Optional


## Self type for the @ref DataDepdendency class.
DataDepdendencyType = TypeVar('DataDepdendencyType', bound='DataDepdendency')


## Notorises a data dependency.
#  A data dependency is a not that byte(s) at a specific location are being utilised by another part of the 
#  system and are more than the function they appear to serve. For example; a protected string might be using
#  the given byte as part of an XOR operation.
#  
#  This is used as a debugging tool, the ELF writer will examine this list before writing and alarm if the 
#  value is about to be rewritten (NOTE it does not check if the value actually changed; it just gets angry
#  if you even try to write to that bytes location).
#
#  This can help solve some difficult to pin down issues.
class DataDepdendency(object):


    ## The default message used if there is not one provided.
    DEFAULT_MESSAGE  = 'There is no recorded description of this depdendency.'


    ## Loads a data dependency from JSON notorisation.
    #  @param cls the type of class invoking this method.
    #  @param json the JSON that contains a definition of the data dependency.
    #  @returns a new instance of the object from the provided JSON.
    @classmethod
    def fromJson(cls, json:dict) -> DataDepdendencyType:
        return cls( json['address'], json['length'], json.get('message', cls.DEFAULT_MESSAGE) )


    ## Creates a new instance of the data depdency object.
    #  @param self the instance of the object that is invoking this method.
    #  @param virtual_memory_address the virtual memory address that the data dependency starts at.
    #  @param length the amount of bytes the data dependency covers.
    #  @param message a message to explain what is using this memory and why.
    def __init__(self, virtual_memory_address:int, length:int, message:str) -> DataDepdendencyType:
        self.start_address = virtual_memory_address
        self.finish_address = virtual_memory_address + length
        self.length = length
        self.message = message


    ## Tests if a given memory range collides with this data dependency.
    #  @param self the instance of the object that is invoking this method.
    #  @param virtual_memory_address address of the memory that we want to test.
    #  @param length the length of the address range to test.
    #  @returns True if there is an overlap between this data dependency and the given range, else False.
    def collides_with(self, virtual_memory_address:int, length:int) -> bool:
        finish_address = virtual_memory_address + length -1
        return (virtual_memory_address >= self.start_address and virtual_memory_address < self.finish_address) or \
               (finish_address > self.start_address and finish_address <= self.finish_address) or \
               (virtual_memory_address < self.start_address and finish_address > self.finish_address)


    ## Converts the object to JSON notation for serialisation.
    #  @param self the instance of the object that is invoking this method.
    #  @returns this object, expressed as a dict object that can be serialised.
    def to_json(self) -> dict:
        return {
            'address': self.start_address,
            'length': self.length,
            'message': self.message
        }




## Self type for the @ref DataDepdendency class.
DataDependencyListType = TypeVar('DataDependencyListType', bound='DataDependencyList')



## Represents a collection of data dependencies
class DataDependencyList(list[DataDepdendency]):

    ## Loads a data dependency from JSON notorisation.
    #  @param cls the type of class invoking this method.
    #  @param json the JSON that contains a definition of the data dependency.
    #  @returns a new instance of the object from the provided JSON.
    @classmethod
    def fromJson(cls, json:dict) -> DataDependencyListType:
        return cls( map(DataDepdendency.fromJson, json) )


    ## Returns an iterator of all data dependencies that collide with the given range.
    #  @param self the instance of the object that is invoking this method.
    #  @param virtual_memory_address address of the memory that we want to test.
    #  @param length the length of the address range to test.
    #  @returns an iterator of all the data dependencies in this list that collide with the given range.
    def collisions(self, virtual_memory_address:int, length:int) -> Iterator[DataDepdendency]:
        for dependency in self:
            if dependency.collides_with(virtual_memory_address, length):
                yield dependency
        return
        yield


    ## Tests if the given range collides with any known data dependencies.
    #  @param self the instance of the object that is invoking this method.
    #  @param virtual_memory_address address of the memory that we want to test.
    #  @param length the length of the address range to test.
    #  @returns True if one or more data dependencies that collide with the request range.
    def has_dependency(self, virtual_memory_address:int, length:int) -> bool:
        for collision in self.collisions(virtual_memory_address, length):
            return True
        return False


    ## Converts the object to JSON notation for serialisation.
    #  @param self the instance of the object that is invoking this method.
    #  @returns this object, expressed as a dict object that can be serialised.
    def to_json(self) -> dict:
        return [ dd.to_json() for dd in self ]