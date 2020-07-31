from abc import ABC
from typing import Dict, List, Union

from banyan.core.exc import BanyanError
from banyan.model import InfoBase, BanyanApiObject
from banyan.model.policy import PolicyInfo
from banyan.model.role import Role, RoleInfo, RoleInfoOrName

InfoObjectOrName = Union[InfoBase, str]


class ServiceBase(ABC):
    class Meta:
        data_class = Role
        info_class = RoleInfo
        arg_type = RoleInfoOrName
        list_uri = '/security_roles'
        delete_uri = '/delete_security_role'
        insert_uri = '/insert_security_role'
        uri_param = 'RoleID'
        obj_name = 'role'

    def __init__(self, client):
        self._client = client
        self._cache: List[InfoBase] = list()
        self._by_name: Dict[str, InfoBase] = dict()
        self._by_id: Dict[str, InfoBase] = dict()

    def list(self) -> list:
        response_json = self._client.api_request('GET', self.Meta.list_uri)
        data: List[InfoBase] = self.Meta.info_class.Schema().load(response_json, many=True)
        self._build_cache(data)
        return data

    def _build_cache(self, info: List[InfoBase]) -> None:
        self._cache = info
        self._by_name = {i.name.lower(): i for i in info}
        self._by_id = {str(i.id).lower(): i for i in info}

    def __getitem__(self, key: str):
        self._ensure_cache()
        try:
            return self._by_name[key.lower()]
        except KeyError:
            try:
                return self._by_id[key.lower()]
            except KeyError:
                raise BanyanError(f'{self.Meta.obj_name} name or ID does not exist: {key}')

    def exists(self, name: str) -> bool:
        self._ensure_cache()
        return name.lower() in self._by_name.keys() or name in self._by_id.keys()

    def _ensure_cache(self) -> None:
        if not self._cache:
            self.list()

    def _ensure_exists(self, name: str) -> None:
        if not self.exists(name):
            raise BanyanError(f'{self.Meta.obj_name} name does not exist: {name}')

    def _ensure_does_not_exist(self, name: str) -> None:
        if self.exists(name):
            raise BanyanError(f'{self.Meta.obj_name} name already exists: {name}')

    def find(self, obj: InfoObjectOrName):
        if isinstance(obj, InfoBase):
            self._ensure_exists(obj.name)
            return obj
        else:
            return self.__getitem__(obj)

    def create(self, obj: BanyanApiObject):
        self._ensure_does_not_exist(obj.name)
        response_json = self._client.api_request('POST',
                                                 self.Meta.insert_uri,
                                                 json=obj.Schema().dump(obj))
        return PolicyInfo.Schema().load(response_json)

    def update(self, obj: BanyanApiObject):
        self._ensure_exists(obj.name)
        response_json = self._client.api_request('POST',
                                                 self.Meta.insert_uri,
                                                 json=obj.Schema().dump(obj))
        return PolicyInfo.Schema().load(response_json)

    def delete(self, obj: InfoObjectOrName):
        obj = self.find(obj)
        json_response = self._client.api_request('DELETE',
                                                 self.Meta.delete_uri,
                                                 params={self.Meta.uri_param: str(obj.id)})
        return json_response['Message']