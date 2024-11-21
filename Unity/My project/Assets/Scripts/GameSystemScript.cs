using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using NativeWebSocket;

public class GameSystemScript : MonoBehaviour
{
    
    public Dictionary<int, GameObject> playerDict;
    public int num_of_players;
    public int my_id = 0;
    public int room_id = 1;
    public Networking networking;
    public WebSocket ws;
    
    // Start is called before the first frame update
    void Start()
    {
        networking = GetComponent<Networking>();
        playerDict = new Dictionary<int, GameObject>(); 
        ws = networking.ws;
        ws.OnMessage += (bytes) =>
        {
            var byteStr = System.Text.Encoding.UTF8.GetString(bytes);
            string[] pos_arr_all = byteStr.Split('/');
            switch (pos_arr_all[0]){
                case "allpos":
                    foreach(string pos_arr_str in pos_arr_all){
                        if (pos_arr_str == "allpos") continue;
                        string[] id_pos = pos_arr_str.Split(',');
                        
                        int id = int.Parse(id_pos[0]);
                        if (id == my_id){
                            if(!playerDict.ContainsKey(id)){
                                GameObject otherPlayer = Resources.Load<GameObject>("player");
                                GameObject clone = Instantiate(otherPlayer, new Vector3(float.Parse(id_pos[1]), float.Parse(id_pos[2]), 0), Quaternion.identity);
                                playerDict.Add(id, clone);
                            }
                            else{
                                // Debug.Log(id_pos[0] +  id_pos[1] + id_pos[2]);
                                playerDict[id].transform.GetComponent<NewBehaviourScript>().targetDirection = (new Vector3(float.Parse(id_pos[1]), float.Parse(id_pos[2]), 0));
                            }
                        }
                        else{
                            if(!playerDict.ContainsKey(id)){
                                GameObject otherPlayer = Resources.Load<GameObject>("OtherPlayer");
                                GameObject clone = Instantiate(otherPlayer, new Vector3(float.Parse(id_pos[1]), float.Parse(id_pos[2]), 0), Quaternion.identity);
                                playerDict.Add(id, clone);
                            }
                            else{
                                // Debug.Log(id_pos[0] +  id_pos[1] + id_pos[2]);
                                playerDict[id].transform.GetComponent<NewBehaviourScript>().targetDirection = (new Vector3(float.Parse(id_pos[1]), float.Parse(id_pos[2]), 0));
                            }
                        }
                    }
                    break;
                default:
                    break;
            };
        };
        // num_of_players = 0;
    }

    // Update is called once per frame
    void Update()
    {

    }
}
