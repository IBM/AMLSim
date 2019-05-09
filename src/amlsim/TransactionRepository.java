package amlsim;

import java.io.BufferedWriter;
import java.io.File;
import java.io.FileWriter;
import java.io.IOException;
import java.util.*;

/**
 * AML Transaction repository (set of transactions) for performance optimizations
 */
public class TransactionRepository {

    public final int size;
    private int index = 0;
//    private DecimalFormat amt_fmt;

    private int count = 0;
    private int limit = Integer.MAX_VALUE;

    private long[] steps;
    private String[] descriptions;
    private float[] amounts;
//    private long[] origIDs;
//    private long[] destIDs;
    private String[] origIDs;
    private String[] destIDs;

    private float[] origBefore;
    private float[] origAfter;
    private float[] destBefore;
    private float[] destAfter;
    private boolean[] isFraud;
    private long[] alertIDs;

    private Map<Long, Integer> txCounter;
    private Map<Long, Integer> fraudCounter;

    public TransactionRepository(int size) {
        this.txCounter = new HashMap<>();
        this.fraudCounter = new HashMap<>();

//        this.amt_fmt = new DecimalFormat("#.#");
//        int precision = 2;
//        this.amt_fmt.setMinimumFractionDigits(precision);

        this.size = size;
        this.steps = new long[size];
        this.descriptions = new String[size];
        this.amounts = new float[size];
        this.origIDs = new String[size];
        this.destIDs = new String[size];

        this.origBefore = new float[size];
        this.origAfter = new float[size];
        this.destBefore = new float[size];
        this.destAfter = new float[size];
        this.isFraud = new boolean[size];
        this.alertIDs = new long[size];
    }

    public void setLimit(int limit){
        this.limit = limit;
    }

//    public void addTransaction(long step, String desc, float amt, long origID, long destID,  float origBefore,
    public void addTransaction(long step, String desc, float amt, String origID, String destID,  float origBefore,
                               float origAfter, float destBefore, float destAfter, boolean fraud, long aid){
        if(count >= limit){
            if(count == limit){
                System.err.println("Warning: the number of output transactions has reached the limit: " + limit);
                flushLog();
                count++;
            }
            return;
        }

        this.steps[index] = step;
        this.descriptions[index] = desc;
        this.amounts[index] = amt;
        this.origIDs[index] = origID;
        this.destIDs[index] = destID;
        this.origBefore[index] = origBefore;
        this.origAfter[index] = origAfter;
        this.destBefore[index] = destBefore;
        this.destAfter[index] = destAfter;
        this.isFraud[index] = fraud;
        this.alertIDs[index] = aid;

        if(fraud){
            fraudCounter.put(step, fraudCounter.getOrDefault(step, 0) + 1);
        }else if(!desc.contains("CASH-")) {
            txCounter.put(step, txCounter.getOrDefault(step, 0) + 1);  // Exclude cash transactions for counter
            count--;
        }

        count++;
        index++;
        if(index >= size){
            flushLog();
        }
    }

    private double getDoublePrecision(double d) {
        // Round down amount to two digits (e.g. 12.3456 --> 12.34)
        // DecimalFormat will not be used because of its computation cost
        return (int)(d * 100) / 100.0;
    }

    public void writeCounterLog(long steps, String fname){
        try {
            BufferedWriter writer = new BufferedWriter(new FileWriter(fname));
            writer.write("step,normal,fraud\n");
            for(long i=0; i<steps; i++){
                int num_tx = txCounter.getOrDefault(i, 0);
                int num_fraud = fraudCounter.getOrDefault(i, 0);
                writer.write(i + "," + num_tx + "," + num_fraud + "\n");
            }
            writer.flush();
        }catch(IOException e){
            e.printStackTrace();
        }
    }

    public void flushLog(){
        // Flush transaction logs to the CSV file

        try {
            FileWriter writer1 = new FileWriter(new File(AMLSim.txLogFileName), true);
            BufferedWriter writer = new BufferedWriter(writer1);

            for(int i = 0; i < this.index; i++){
                writer.write(steps[i] + "," + descriptions[i] + "," + getDoublePrecision(amounts[i]) + "," +
                        origIDs[i] + "," + getDoublePrecision(origBefore[i]) + "," + getDoublePrecision(origAfter[i]) + "," +
                        destIDs[i] + "," + getDoublePrecision(destBefore[i]) + "," + getDoublePrecision(destAfter[i]) + "," +
                        (isFraud[i] ? "1" : "0") + "," + alertIDs[i] + "\n");
            }
            writer.flush();
            writer.close();
        } catch (IOException e) {
            e.printStackTrace();
        }
        index = 0;
    }

}
