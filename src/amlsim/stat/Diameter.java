package amlsim.stat;

import java.io.IOException;
import java.util.*;
import it.unimi.dsi.webgraph.*;
import it.unimi.dsi.webgraph.algo.HyperBall;

/**
 * Compute diameter and average distance of the transaction graph
 */
public class Diameter {

    private ArrayListMutableGraph graph;  // Transaction graph (WebGraph)
//    private Map<Long, Integer> id2idx;  // Account ID --> Index of Graph
    private Map<String, Integer> id2idx;  // Account ID --> Index of Graph

    private Map<Integer, Set<Integer>>  adj;  // Adjacency set (account index --> neighbor account index)

    public Diameter(int numAccounts){
        this.graph = new ArrayListMutableGraph(numAccounts);
        this.id2idx = new HashMap<>(numAccounts);
        this.adj = new HashMap<>(numAccounts);
    }

    /**
     * Add an edge to the internal transaction graph
     * @param srcID source account ID
     * @param dstID destination account ID
     */
//    public void addEdge(long srcID, long dstID){
    public void addEdge(String srcID, String dstID){
        if(!id2idx.containsKey(srcID)){
            int idx = id2idx.size();
            id2idx.put(srcID, idx);
            adj.put(idx, new HashSet<>());
        }
        if(!id2idx.containsKey(dstID)){
            int idx = id2idx.size();
            id2idx.put(dstID, idx);
            adj.put(idx, new HashSet<>());
        }
        int srcIdx = id2idx.get(srcID);
        int dstIdx = id2idx.get(dstID);
        if(!adj.get(srcIdx).contains(dstIdx)) {  // If this edge is not yet added, add it
            graph.addArc(srcIdx, dstIdx);
            adj.get(srcIdx).add(dstIdx);
        }
    }

    /**
     * Compute diameter and average length with HyperANF
     * @return Diameter and average length as an array of double values
     */
    public double[] computeDiameter(){
        int log2m = 10;  // Register length exponent: it affects elapsed time, memory consumption and precision)
        int th = 4;  // Number of threads
        int maxDistance = 50;  // Limit of distance
        double aver = 0.0;
        double[] result = new double[2];

        try {
            ImmutableGraph g = graph.immutableView();
            HyperBall hyperanf = new HyperBall(g, null, log2m, null, th, 0, 0, false);
            hyperanf.init();
            int connectedNodes = g.numNodes();

            long start = System.currentTimeMillis();
            int prev = connectedNodes;
            for(int i=0; i<maxDistance; i++){
                hyperanf.iterate();
                int mod = hyperanf.modified();
                int num = prev - mod;

                if(i == 0){
                    connectedNodes -= num;
                }else{
                    aver += i * (double)num / connectedNodes;
                }

//                System.out.println("Step:" + i + " Average Distance:" + aver);
                prev = mod;
                if(mod == 0){  // reached all vertices
                    System.out.println("Diameter: " + i);
                    result[0] = i;
                    break;
                }
            }
            System.out.println("Average Distance: " + aver);
            result[1] = aver;

            hyperanf.close();
            long end = System.currentTimeMillis();
            System.out.println("Elapsed Time: " + (end - start)/1000 + "s");
            return result;

        } catch (IOException e) {
            System.err.println("Cannot load and compute graph data");
            e.printStackTrace();
            return null;
        }
    }

}

