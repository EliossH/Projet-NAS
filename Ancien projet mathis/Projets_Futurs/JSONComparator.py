from jsondiff import diff
import json

changes = []

def retrieve_link_and_data(lst, parent):
    if isinstance(lst[1], dict):
        for key in lst[1].keys():
            if str(key) == "$insert":
                try:
                    inse, dele = lst[1].keys()
                except:
                    inse, dele = list(lst[1].keys())[0], None
                data = parent[:]
                if dele:
                    for ind in lst[1][dele]:
                        data.pop(ind)
                for i, val in lst[1][inse]:
                    data.insert(i, val)
                changes.append([lst[0], data])
                break
            else:
                lst[0].append(str(key))
                retrieve_link_and_data([lst[0], lst[1][key]], parent[key])
    else:
        changes.append(lst)
        return


def differences(old_dict, new_dict):
    differences = diff(old_dict, new_dict)
    for key in differences:
        retrieve_link_and_data([[str(key)], differences[key]], old_dict[key])
    print(differences)
    print("\n")
    print(changes)


f1 = open('config.json')
f2 = open('complete.json')
config = json.load(f1)
complete = json.load(f2)
differences(config, complete)
