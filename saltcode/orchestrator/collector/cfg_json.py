test_json={
  "tags": ["hello-without"],
  "node_list": ["freerad4"],
  "collectors": {
    "enabled":True,
    "interval": "30",
    "plugins": [
      {
        "name": "cpu",
        "enabled": True,
        "interval": "30",
        "tags": ["hello-within"],
        "targets":["elasticsearch1"]
      },
     { 
        "name":"cpu_static",
        "enabled":True,
        "interval":"15",
        "targets":["elasticsearch2"]
     },
     { 
        "name":"tcp_stats",
        "enabled":False,
        "interval":"16",
        "targets":["elasticsearch3", "elasticsearch2"]
     },
     { 
        "name":"nic_stats",
        "enabled":True,
        "interval":"16",
        "targets":["elasticsearch1", "elasticsearch2", "elasticsearch3"]
     },
     { 
        "name":"ram_usage",
        "enabled":True,
        "interval":"17",
        "targets":["elasticsearch1"]
     },
     { 
        "name":"disk_stat",
        "enabled":True,
        "interval":"15",
        "targets":["elasticsearch2"]
     },
     { 
        "name":"disk_usage",
        "enabled":True,
        "interval":"15",
        "targets":["elasticsearch1"]
     }
    ],
    "targets": [
      {
        "name": "elasticsearch1",
        "type": "elasticsearch",
        "host": "10.11.0.134",
        "port": "9200",
        "index": "elast1"
      },
      {
        "name": "elasticsearch2",
        "type": "elasticsearch",
        "host": "10.11.0.134",
        "port": "9200",
        "index": "elast2"
      },
      {
        "name": "elasticsearch3",
        "type": "elasticsearch",
        "host": "10.11.0.134",
        "port": "9200",
        "index": "elast3"
      }
    ]
    
  }
}
