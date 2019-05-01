package amlsim;

import java.io.*;
import java.nio.file.*;
import java.util.*;

import org.json.*;

public class SchemaLoader {

    private JSONObject obj;

    public static String loadTextFile(String fname) throws IOException{
        Path file = Paths.get(fname);
        byte[] bytes = Files.readAllBytes(file);
        return new String(bytes);
    }

    public void loadJSON(String fname){
        try{
            String jsonStr = loadTextFile(fname);
            obj = new JSONObject(jsonStr);
        }catch (IOException e){
            System.err.println("Cannot load JSON file: " + fname);
            e.printStackTrace();
        }
    }

    private JSONObject getAccountSchema(){
        return obj.getJSONObject("account");
    }

    // acct_id,tax_id,alt_id,dsply_nm,type,initial_deposit,balance,net_wrth_prd_end,acct_peer_grp_intrl_id,acct_rptng_crncy,branch_id,relationship_mgr_id,open_dt,close_dt,close_reason,acct_stat,acct_stat_dt,acct_last_updated_ts,acct_segment,dormant_status_flag,frozen_status_flag,acct_efctv_risk,acct_bus_risk,cstm_risk1,past_confirmed_fraud,past_suspected_fraud,prior_sar_count,is_sar
    public List<String> getHeaders(String dataName){
        List<String> result = new ArrayList<>();
        JSONArray fields = obj.getJSONArray(dataName);
        for (int i = 0; i < fields.length(); i++) {
            String name = fields.getJSONObject(i).getString("name");
            result.add(name);
        }
        return result;
    }
}


