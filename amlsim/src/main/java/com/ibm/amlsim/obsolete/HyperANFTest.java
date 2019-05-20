package com.ibm.amlsim.obsolete;

import it.unimi.dsi.webgraph.BVGraph;
import it.unimi.dsi.webgraph.algo.*;
import java.io.*;

public class HyperANFTest {

    private static final int DISTANCE = 50;

    public static void main(String[] args) {
        try{
            BVGraph graph = BVGraph.load(args[0], 2);
            System.out.println("Nodes: " + graph.numNodes());
            HyperBall hyperanf = new HyperBall(graph, 12);
            hyperanf.init();
            for(int i=0; i<DISTANCE; i++){
                hyperanf.iterate();
                int mod = hyperanf.modified();
                System.out.println(i + " " + mod);
                if(mod == 0){
                    System.out.println("Max Diameter: " + i);
                    break;
                }
            }
            hyperanf.close();

            NeighbourhoodFunction nf = new NeighbourhoodFunction();
            double[] nfs = NeighbourhoodFunction.compute(graph);
            double aver_dist = NeighbourhoodFunction.averageDistance(nfs);
            System.out.println("Average Diameter: " + aver_dist);
        }catch (IOException e){
            e.printStackTrace();
        }
    }

}

