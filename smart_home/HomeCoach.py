"""
coding=utf-8
"""
import warnings, time

from . import NoDevice, postRequest, todayStamps, _BASE_URL

_GETHOMECOACHNDATA_REQ = _BASE_URL + "api/gethomecoachsdata"

class HomeCoachData:
    """
    List the Healthy Home Coach devices (devices and modules)

    Args:
        authData (ClientAuth): Authentication information with a working access Token
    """
    def __init__(self, authData):
        self.getAuthToken = authData.accessToken
        postParams = {
                "access_token" : self.getAuthToken
                }
        resp = postRequest(_GETHOMECOACHNDATA_REQ, postParams)
        self.rawData = resp['body']['devices']
        if not self.rawData : raise NoDevice("No home coach device available")
        self.devices = { d['_id'] : d for d in self.rawData }
        self.modules = dict()
        for i in range(len(self.rawData)):
            for m in self.rawData[i]['modules']:
                self.modules[ m['_id'] ] = m
                self.modules[ m['_id'] ][ 'main_device' ] = self.rawData[i]['_id']
        self.default_device = list(self.devices.values())[0]['module_name']

    def modulesNamesList(self, device=None):
        res = [m['module_name'] for m in self.modules.values()]
        if device:
            res.append(self.deviceByName(device)['name'])
        else:
            for id,device in self.devices.items():
                res.append(device['name'])
        return res

    def deviceByName(self, device=None):
        if not device : device = self.default_device
        for i,s in self.devices.items():
            if s['name'] == device :
                return self.devices[i]
        return None

    def deviceById(self, sid):
        return None if sid not in self.devices else self.devices[sid]

    def moduleByName(self, module, device=None):
        s = None
        if device :
            s = self.deviceByName(device)
            if not s : return None
            elif s['module_name'] == module:
                return s
        else:
            for id, device in self.devices.items():
                if device['module_name'] == module:
                    return device
        for m in self.modules:
            mod = self.modules[m]
            if mod['module_name'] == module :
                if not s or mod['main_device'] == s['_id'] : return mod
        return None

    def moduleById(self, mid, sid=None):
        s = self.deviceById(sid) if sid else None
        if mid in self.modules :
            if s:
                for module in s['modules']:
                    if module['_id'] == mid:
                        return module
            else:
                return self.modules[mid]

    def monitoredConditions(self, module):
        mod = self.moduleByName(module)
        conditions = []
        for cond in mod['data_type']:
            conditions.append(cond.lower())
        conditions.append('wifi_status')
        return conditions

    def lastData(self, device=None, exclude=0):
        s = self.deviceByName(device)
        if not s : return None
        lastD = dict()
        # Define oldest acceptable sensor measure event
        limit = (time.time() - exclude) if exclude else 0
        ds = s['dashboard_data']
        if ds['time_utc'] > limit :
            lastD[s['name']] = ds.copy()
            lastD[s['name']]['When'] = lastD[s['name']].pop("time_utc")
            lastD[s['name']]['wifi_status'] = s['wifi_status']
        for module in s["modules"]:
            ds = module['dashboard_data']
            if ds['time_utc'] > limit :
                lastD[module['name']] = ds.copy()
                lastD[module['name']]['When'] = lastD[module['name']].pop("time_utc")
        return lastD

    def checkNotUpdated(self, device=None, delay=3600):
        res = self.lastData(device)
        ret = []
        for mn,v in res.items():
            if time.time()-v['When'] > delay : ret.append(mn)
        return ret if ret else None

    def checkUpdated(self, device=None, delay=3600):
        res = self.lastData(device)
        ret = []
        for mn,v in res.items():
            if time.time()-v['When'] < delay : ret.append(mn)
        return ret if ret else None

